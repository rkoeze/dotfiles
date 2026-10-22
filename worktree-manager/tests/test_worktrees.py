"""Integration tests using disposable repositories and only Python's standard library."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "worktrees.py"
spec = importlib.util.spec_from_file_location("worktrees", SCRIPT)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mise-worktrees-python-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repos = self.root / "repos with spaces"
        self.tasks = self.root / "tasks with spaces"
        self.repos.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            WT_REPOS_ROOT=str(self.repos), WT_TASKS_ROOT=str(self.tasks),
            GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Worktree Test", GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Worktree Test", GIT_COMMITTER_EMAIL="test@example.invalid",
            PYTHONDONTWRITEBYTECODE="1",
        )
        self.init_repo("api", "main")
        self.init_repo("auth", "master")
        self.init_repo("front end", "main")

    def run_command(self, command, *, input="", ok=True, env=None, cwd=None):
        result = subprocess.run(
            list(map(str, command)), input=input, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env or self.env, cwd=cwd or self.root,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def git(self, repo, *args):
        return self.run_command(["git", "-C", repo, *args]).stdout.strip()

    def wt(self, *args, **kwargs):
        return self.run_command([sys.executable, SCRIPT, *args], **kwargs)

    def init_repo(self, name, branch):
        repo = self.repos / name
        self.git(self.root, "init", "-q", "-b", branch, repo)
        (repo / "tracked").write_text("initial\n")
        self.git(repo, "add", "tracked")
        self.git(repo, "commit", "-qm", "initial")
        return repo

    def assert_worktree(self, task, name, branch=None):
        path = self.tasks / task / name
        self.assertTrue((path / ".git").is_file())
        self.assertEqual(self.git(path, "branch", "--show-current"), branch or task)
        return path

    def test_creation_overlap_add_list_status_and_original_checkout(self):
        api = self.repos / "api"
        self.git(api, "switch", "-qc", "original")
        (api / "original-only").write_text("only on original branch\n")
        self.git(api, "add", "original-only")
        self.git(api, "commit", "-qm", "original branch commit")
        (api / "tracked").write_text("original dirty change\n")
        (api / "untracked").write_text("valuable original data\n")
        before = self.git(api, "status", "--porcelain")
        self.assertIn("No task workspaces", self.wt("list").stdout)
        self.assertFalse(self.tasks.exists())
        self.wt("create", "first", "api", "auth")
        first = self.assert_worktree("first", "api")
        self.assertEqual(self.git(first, "rev-parse", "HEAD"), self.git(api, "rev-parse", "main"))
        self.assertFalse((first / "original-only").exists())
        self.wt("create", "second", "api")
        self.assert_worktree("second", "api")
        self.wt("add", "first", "front end", "front end")
        self.assert_worktree("first", "front end")
        self.assertIn("already included", self.wt("create", "first", "api", "api").stdout)
        listing = self.wt("list").stdout
        for name in ("first", "second", "api", "auth", "front end"):
            self.assertIn(name, listing)
        self.assertIn("## first", self.wt("status", "first").stdout)
        self.assertEqual(self.git(api, "branch", "--show-current"), "original")
        self.assertEqual(self.git(api, "status", "--porcelain"), before)

    def checkout_remote(self, name="api", remote="origin"):
        upstream = self.init_repo("upstream", "main")
        self.git(upstream, "switch", "-qc", "feature/pr-fix")
        (upstream / "tracked").write_text("PR changes\n")
        self.git(upstream, "commit", "-qam", "PR commit")
        self.git(upstream, "tag", "pr-tag")
        commit = self.git(upstream, "rev-parse", "HEAD")
        self.git(upstream, "switch", "-q", "main")
        self.git(self.repos / name, "remote", "add", remote, upstream)
        return upstream, commit

    def test_checkout_fetches_exact_branch_and_preserves_original_checkout_and_refs(self):
        api = self.repos / "api"
        _, commit = self.checkout_remote()
        initial = self.git(api, "rev-parse", "HEAD")
        self.git(api, "update-ref", "refs/remotes/origin/feature/pr-fix", initial)
        (api / "tracked").write_text("dirty original\n")
        (api / "untracked").write_text("valuable original data\n")
        before = self.git(api, "status", "--porcelain")
        result = self.wt("checkout", "feature/pr-fix", "api")
        path = self.assert_worktree("feature-pr-fix", "api", branch="feature/pr-fix")
        self.assertIn("origin/feature/pr-fix", result.stdout)
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), commit)
        self.assertEqual((path / "tracked").read_text(), "PR changes\n")
        self.assertEqual(self.git(path, "status", "--porcelain"), "")
        self.assertEqual(self.git(api, "branch", "--show-current"), "main")
        self.assertEqual(self.git(api, "rev-parse", "HEAD"), initial)
        self.assertEqual(self.git(api, "status", "--porcelain"), before)
        self.assertEqual(self.git(api, "rev-parse", "refs/remotes/origin/feature/pr-fix"), initial)
        self.assertEqual(self.git(api, "tag", "--list"), "")
        self.assertEqual(self.git(api, "config", "--get-regexp", "^remote.origin.fetch$"),
                         "remote.origin.fetch +refs/heads/*:refs/remotes/origin/*")
        self.run_command(["git", "-C", path, "rev-parse", "--verify", "@{upstream}"], ok=False)
        self.assertIn("feature-pr-fix", self.wt("list").stdout)
        self.assertIn("## feature/pr-fix", self.wt("status", "feature-pr-fix").stdout)
        self.wt("remove", "feature-pr-fix")
        self.assertEqual(self.git(api, "rev-parse", "feature/pr-fix"), commit)
        # Re-running after removal must not reset the preserved branch.
        self.wt("checkout", "feature/pr-fix", "api", ok=False)
        self.assertFalse((self.tasks / "feature-pr-fix").exists())

    def test_checkout_custom_remote_and_existing_workspace(self):
        upstream, commit = self.checkout_remote(name="front end", remote="upstream")
        self.git(self.repos / "auth", "remote", "add", "upstream", upstream)
        self.wt("checkout", "feature/pr-fix", "auth", "--remote", "upstream")
        self.wt("checkout", "feature/pr-fix", "front end", "--remote", "upstream")
        path = self.assert_worktree("feature-pr-fix", "front end", branch="feature/pr-fix")
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), commit)
        self.assert_worktree("feature-pr-fix", "auth", branch="feature/pr-fix")

    def test_checkout_picker_multiple_repos_and_idempotent_retry(self):
        upstream, commit = self.checkout_remote()
        self.git(self.repos / "auth", "remote", "add", "origin", upstream)
        result = self.wt("checkout", "feature/pr-fix", input="1 2 2\n")
        self.assertIn("1) api", result.stdout)
        self.assertIn("2) auth", result.stdout)
        self.assertIn("3) front end", result.stdout)
        for repo in ("api", "auth"):
            path = self.assert_worktree("feature-pr-fix", repo, branch="feature/pr-fix")
            self.assertEqual(self.git(path, "rev-parse", "HEAD"), commit)
        self.assertFalse((self.tasks / "feature-pr-fix/front end").exists())
        # Existing members are not fetched, reset, or switched, even with new remote commits.
        self.git(upstream, "switch", "-q", "feature/pr-fix")
        (upstream / "tracked").write_text("new remote commit\n")
        self.git(upstream, "commit", "-qam", "update PR")
        result = self.wt("checkout", "feature/pr-fix", "api", "auth")
        self.assertIn("already included", result.stdout)
        self.assertEqual(self.git(self.tasks / "feature-pr-fix/api", "rev-parse", "HEAD"), commit)

    def test_checkout_partial_failure_and_retry_without_default_fallback(self):
        upstream, commit = self.checkout_remote()
        auth = self.repos / "auth"
        self.git(auth, "remote", "add", "origin", auth)  # No PR branch on this remote.
        result = self.wt("checkout", "feature/pr-fix", "auth", "api", ok=False)
        self.assertIn("FAIL auth", result.stderr)
        self.assertIn("successful worktrees and branches were kept", result.stderr)
        self.assert_worktree("feature-pr-fix", "api", branch="feature/pr-fix")
        self.assertFalse((self.tasks / "feature-pr-fix/auth").exists())
        self.run_command(["git", "-C", auth, "show-ref", "--verify",
                          "refs/heads/feature/pr-fix"], ok=False)
        self.git(auth, "remote", "set-url", "origin", upstream)
        self.wt("checkout", "feature/pr-fix", "api", "auth")
        path = self.assert_worktree("feature-pr-fix", "auth", branch="feature/pr-fix")
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), commit)

    def test_checkout_fetch_failure_does_not_use_stale_refs_or_create_workspace(self):
        api = self.repos / "api"
        upstream, _ = self.checkout_remote()
        self.git(api, "fetch", "origin", "feature/pr-fix")
        self.git(upstream, "branch", "-D", "feature/pr-fix")
        self.wt("checkout", "feature/pr-fix", "api", ok=False)
        self.assertFalse(self.tasks.exists())
        self.run_command(["git", "-C", api, "show-ref", "--verify",
                          "refs/heads/feature/pr-fix"], ok=False)

    def test_checkout_refuses_existing_branches_without_fetching_or_resetting(self):
        api = self.repos / "api"
        self.git(api, "branch", "feature/pr-fix")
        initial = self.git(api, "rev-parse", "feature/pr-fix")
        result = self.wt("checkout", "feature/pr-fix", "api", ok=False)
        self.assertIn("already exists", result.stderr)
        result = self.wt("checkout", "main", "api", ok=False)
        self.assertIn(f"checked out at {api}", result.stderr)
        self.assertFalse(self.tasks.exists())
        self.assertEqual(self.git(api, "rev-parse", "feature/pr-fix"), initial)
        self.assertEqual(self.git(api, "branch", "--show-current"), "main")

    def test_checkout_refuses_existing_destinations_and_unmanaged_workspaces(self):
        self.wt("create", "review", "auth")
        destination = self.tasks / "review/api"
        for kind in ("file", "directory", "symlink"):
            with self.subTest(kind=kind):
                if kind == "file":
                    destination.write_text("keep\n")
                elif kind == "directory":
                    destination.mkdir()
                else:
                    destination.symlink_to(self.repos / "api", target_is_directory=True)
                result = self.wt("checkout", "review", "api", ok=False)
                self.assertIn("Destination already exists", result.stderr)
                self.assertTrue(manager.exists(destination))
                if kind == "directory":
                    destination.rmdir()
                else:
                    destination.unlink()
        unrelated = self.tasks / "unrelated"
        unrelated.mkdir()
        self.wt("checkout", "unrelated", "api", ok=False)
        self.assertEqual(list(unrelated.iterdir()), [])
        (self.tasks / "alias").symlink_to(self.tasks / "review", target_is_directory=True)
        self.wt("checkout", "alias", "api", ok=False)
        self.assert_worktree("review", "auth")
        self.git(self.tasks / "review/auth", "switch", "-qc", "manually-changed")
        self.wt("checkout", "review", "auth", ok=False)
        self.assert_worktree("review", "auth", branch="manually-changed")

    def test_checkout_normalized_folder_collision_does_not_mix_branches(self):
        upstream, _ = self.checkout_remote()
        self.git(upstream, "branch", "feature-pr-fix", "feature/pr-fix")
        self.git(self.repos / "auth", "remote", "add", "origin", upstream)
        self.wt("checkout", "feature/pr-fix", "api")
        result = self.wt("checkout", "feature-pr-fix", "auth", ok=False)
        self.assertIn("different branch", result.stderr)
        self.assertFalse((self.tasks / "feature-pr-fix/auth").exists())
        self.assert_worktree("feature-pr-fix", "api", branch="feature/pr-fix")

    def test_checkout_invalid_inputs_have_no_side_effects(self):
        self.checkout_remote()
        for branch in ("missing", "feature/pr-fix:other", "feature/*", "a..b", "@{-1}",
                       "has space", "-option", "feature//fix", "../escape", "/absolute",
                       "a.lock", "a.", "HEAD"):
            with self.subTest(branch=branch):
                self.wt("checkout", "--", branch, "api", ok=False)
                self.assertFalse(self.tasks.exists())
        for remote in ("missing", "--upload-pack=bad", str(self.repos / "upstream")):
            with self.subTest(remote=remote):
                self.wt("checkout", "feature/pr-fix", "api", f"--remote={remote}", ok=False)
        self.wt("checkout", "feature/pr-fix", "missing", ok=False)
        self.wt("checkout", ok=False)
        for selection in ("", "\n", "0\n", "999999\n", "x\n"):
            self.wt("checkout", "feature/pr-fix", input=selection, ok=False)
        for variable, value in (("WT_REPOS_ROOT", "relative"), ("WT_TASKS_ROOT", "relative"),
                                ("WT_TASKS_ROOT", str(self.repos / "api/tasks"))):
            self.wt("checkout", "feature/pr-fix", "api",
                    env=dict(self.env, **{variable: value}), ok=False)
        self.assertFalse(self.tasks.exists())
        self.wt("checkout", "--help")

    def test_checkout_native_failure_keeps_recoverable_workspace_and_existing_refs(self):
        api = self.repos / "api"
        self.checkout_remote()
        self.git(api, "branch", "feature/pr-fix/child")
        self.wt("checkout", "feature/pr-fix", "api", ok=False)
        self.assertFalse((self.tasks / "feature-pr-fix/api").exists())
        self.assertTrue(manager.managed(self.tasks / "feature-pr-fix"))
        self.git(api, "show-ref", "--verify", "refs/heads/feature/pr-fix/child")
        self.wt("remove", "feature-pr-fix")

    @unittest.skipUnless(shutil.which("mise"), "Mise is not installed")
    def test_mise_checkout_argument_forwarding_and_picker(self):
        upstream, commit = self.checkout_remote(name="front end", remote="upstream")
        self.git(self.repos / "api", "remote", "add", "upstream", upstream)
        self.run_command(["mise", "run", "wt:checkout", "feature/pr-fix",
                          "front end", "--remote", "upstream"])
        path = self.assert_worktree("feature-pr-fix", "front end", branch="feature/pr-fix")
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), commit)
        self.run_command(["mise", "run", "wt:checkout", "feature/pr-fix",
                          "--remote", "upstream"], input="1 3\n")
        self.assert_worktree("feature-pr-fix", "api", branch="feature/pr-fix")

    def test_interactive_selection_and_add(self):
        result = self.wt("create", "menu", input="1 3 3\n")
        self.assertIn("1) api", result.stdout)
        self.assertIn("2) auth", result.stdout)
        self.assertIn("3) front end", result.stdout)
        self.assert_worktree("menu", "api")
        self.assert_worktree("menu", "front end")
        self.assertFalse((self.tasks / "menu/auth").exists())
        self.wt("add", "menu", input="2\n")
        self.assert_worktree("menu", "auth")

    def test_invalid_selections_and_inputs_have_no_side_effects(self):
        for selection in ("", "\n", "0\n", "999999\n", "x\n", "1;touch bad\n"):
            with self.subTest(selection=selection):
                self.wt("create", "invalid-menu", input=selection, ok=False)
                self.assertFalse((self.tasks / "invalid-menu").exists())
        for task in ("../escape", "/absolute", "-option", "has space", "a..b", "a.lock", "a/child", "a.", "HEAD"):
            with self.subTest(task=task):
                self.wt("create", task, "api", ok=False)
        self.wt("create", "unknown", "api", "missing", ok=False)
        self.wt("add", "missing", "api", ok=False)
        self.wt("status", "missing", ok=False)
        self.wt("remove", "missing", ok=False)
        self.assertFalse(self.tasks.exists())
        for args in ((), ("unknown",), ("list", "extra"), ("status", "task", "extra")):
            with self.subTest(args=args):
                self.wt(*args, ok=False)
        self.wt("--help")
        self.wt("create", "--help")

    def test_root_validation(self):
        for tasks_root in (str(self.repos / "api/tasks"), str(self.repos / "."), "relative"):
            with self.subTest(tasks_root=tasks_root):
                env = dict(self.env, WT_TASKS_ROOT=tasks_root)
                self.wt("create", "unsafe", "api", env=env, ok=False)
        self.wt("create", "unsafe", "api", env=dict(self.env, WT_REPOS_ROOT="relative"), ok=False)
        self.assertFalse((self.repos / "api/tasks").exists())
        self.assertFalse((self.repos / "unsafe").exists())
        self.assertFalse(self.tasks.exists())

    def test_default_branches_and_remote_head_discovery(self):
        custom = self.init_repo("custom", "develop")
        self.git(custom, "remote", "add", "origin", custom)
        self.git(custom, "fetch", "-q", "origin")
        self.git(custom, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/develop")
        upstream = self.init_repo("upstream", "trunk")
        self.git(upstream, "remote", "add", "other", upstream)
        self.wt("create", "defaults", "api", "auth", "custom", "upstream")
        for repo, branch in (("api", "main"), ("auth", "master"), ("custom", "develop"), ("upstream", "trunk")):
            with self.subTest(repo=repo):
                path = self.assert_worktree("defaults", repo)
                self.assertEqual(self.git(path, "rev-parse", "HEAD"),
                                 self.git(self.repos / repo, "rev-parse", branch))

    def test_offline_remote_falls_back_to_local_default(self):
        self.git(self.repos / "api", "remote", "add", "origin", self.root / "nonexistent")
        self.wt("create", "offline", "api")
        self.assert_worktree("offline", "api")

    def test_missing_defaults_empty_workspace_and_branch_reuse(self):
        odd = self.init_repo("odd", "develop")
        result = self.wt("create", "empty", "odd", ok=False)
        self.assertIn("Cannot determine default branch", result.stderr)
        self.wt("remove", "empty")
        self.assertFalse((self.tasks / "empty").exists())
        self.git(odd, "branch", "reuse")
        self.assertIn("reused reuse", self.wt("create", "reuse", "odd").stdout)

    def test_recorded_but_missing_remote_default_does_not_fall_back(self):
        api = self.repos / "api"
        self.git(api, "remote", "add", "origin", api)
        self.git(api, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/missing")
        result = self.wt("create", "missing-default", "api", ok=False)
        self.assertIn("fetch it first", result.stderr)
        self.assertFalse((self.tasks / "missing-default/api").exists())

    def test_source_dotgit_file_and_shared_repository_conflict(self):
        self.git(self.repos / "api", "worktree", "add", "-qb", "source-alias", self.repos / "linked")
        self.wt("create", "file-source", "linked")
        self.assert_worktree("file-source", "linked")
        self.wt("create", "same", "api")
        result = self.wt("add", "same", "linked", ok=False)
        self.assertIn("checked out at", result.stderr)
        self.assertIn(str(self.tasks / "same/api"), result.stderr)

    def test_conflict_partial_success_and_retry(self):
        api = self.repos / "api"
        outside = self.root / "outside"
        self.git(api, "worktree", "add", "-qb", "conflict", outside)
        result = self.wt("create", "conflict", "auth", "api", ok=False)
        self.assertIn(str(outside), result.stderr)
        self.assertIn("successful worktrees and branches were kept", result.stderr)
        self.assert_worktree("conflict", "auth")
        self.assertFalse((self.tasks / "conflict/api").exists())
        self.git(api, "worktree", "remove", outside)
        result = self.wt("add", "conflict", "api")
        self.assertIn("reused conflict", result.stdout)
        self.assert_worktree("conflict", "api")

    def test_native_add_failure_does_not_prevent_other_repositories(self):
        # A child ref prevents Git from creating the branch native in this repository.
        self.git(self.repos / "api", "branch", "native/child")
        result = self.wt("create", "native", "api", "auth", ok=False)
        self.assertIn("FAIL api", result.stderr)
        self.assertIn("OK auth", result.stdout)
        self.assert_worktree("native", "auth")
        self.git(self.repos / "api", "show-ref", "--verify", "refs/heads/native/child")
        self.assertTrue((self.tasks / "native" / manager.MARKER).is_file())

    def test_removal_preflight_protects_every_worktree_and_every_change_type(self):
        self.wt("create", "dirty", "api", "auth")
        auth = self.tasks / "dirty/auth"
        (self.repos / "auth/.git/info/exclude").write_text("local.secret\n")
        for kind in ("unstaged", "staged", "untracked", "ignored"):
            with self.subTest(kind=kind):
                if kind in ("unstaged", "staged"):
                    (auth / "tracked").write_text("valuable change\n")
                    if kind == "staged":
                        self.git(auth, "add", "tracked")
                else:
                    (auth / ("local.secret" if kind == "ignored" else "untracked")).write_text("valuable\n")
                self.assertIn("## dirty", self.wt("status", "dirty").stdout)
                result = self.wt("remove", "dirty", ok=False)
                self.assertIn("UNSAFE auth", result.stderr)
                self.assertIn("Nothing removed", result.stderr)
                self.assert_worktree("dirty", "api")  # Clean first repo must survive.
                self.assert_worktree("dirty", "auth")
                if kind in ("unstaged", "staged"):
                    self.git(auth, "restore", "--staged", "--worktree", "tracked")
                else:
                    (auth / ("local.secret" if kind == "ignored" else "untracked")).unlink()
        self.wt("remove", "dirty")
        self.assertFalse((self.tasks / "dirty").exists())
        for repo in ("api", "auth"):
            self.git(self.repos / repo, "show-ref", "--verify", "refs/heads/dirty")
        self.wt("remove", "dirty", ok=False)

    def test_locked_and_unrecognized_entries_block_entire_removal(self):
        self.wt("create", "safe", "api", "auth")
        self.git(self.repos / "auth", "worktree", "lock", self.tasks / "safe/auth")
        result = self.wt("remove", "safe", ok=False)
        self.assertIn("locked", result.stderr)
        self.assert_worktree("safe", "api")
        self.git(self.repos / "auth", "worktree", "unlock", self.tasks / "safe/auth")
        note = self.tasks / "safe/notes.txt"
        note.write_text("keep\n")
        self.wt("remove", "safe", ok=False)
        self.assertEqual(note.read_text(), "keep\n")
        self.assert_worktree("safe", "api")
        note.unlink()
        self.wt("remove", "safe")

    def test_branch_commits_survive_removal_and_recreation(self):
        self.git(self.repos / "auth", "branch", "reuse", "master")
        self.assertIn("reused reuse", self.wt("create", "reuse", "auth").stdout)
        path = self.tasks / "reuse/auth"
        (path / "tracked").write_text("task commit\n")
        self.git(path, "commit", "-qam", "task work")
        saved = self.git(path, "rev-parse", "HEAD")
        self.wt("remove", "reuse")
        self.wt("create", "reuse", "auth")
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), saved)

    def test_unrelated_directories_symlinks_and_conflicting_destinations(self):
        unrelated = self.tasks / "unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "file").write_text("keep\n")
        self.wt("create", "unrelated", "api", ok=False)
        self.wt("remove", "unrelated", ok=False)
        self.assertEqual((unrelated / "file").read_text(), "keep\n")
        self.wt("create", "first", "auth")
        alias = self.tasks / "alias"
        alias.symlink_to(self.tasks / "first", target_is_directory=True)
        self.wt("remove", "alias", ok=False)
        self.wt("create", "alias", "api", ok=False)
        self.assert_worktree("first", "auth")
        destination = self.tasks / "first/api"
        for kind in ("symlink", "directory", "file"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    destination.symlink_to(self.repos / "api", target_is_directory=True)
                elif kind == "directory":
                    destination.mkdir()
                else:
                    destination.write_text("keep\n")
                self.wt("add", "first", "api", ok=False)
                if kind == "directory":
                    destination.rmdir()
                else:
                    destination.unlink()

    def test_existing_prefixed_worktrees_are_not_renamed(self):
        workspace = self.tasks / "legacy"
        workspace.mkdir(parents=True)
        (workspace / manager.MARKER).write_text(manager.VERSION + "\n")
        self.git(self.repos / "api", "worktree", "add", "-b", "task/legacy", workspace / "api", "main")
        self.wt("create", "legacy", "api")
        self.assert_worktree("legacy", "api", branch="task/legacy")
        self.wt("add", "legacy", "auth")
        self.assert_worktree("legacy", "auth")
        self.assertIn("task/legacy", self.wt("status", "legacy").stdout)
        self.wt("remove", "legacy")
        self.git(self.repos / "api", "show-ref", "--verify", "refs/heads/task/legacy")

    def test_existing_default_branch_conflict_does_not_change_original(self):
        result = self.wt("create", "main", "api", ok=False)
        self.assertIn("Branch main is checked out at", result.stderr)
        self.assertFalse((self.tasks / "main/api").exists())
        self.assertEqual(self.git(self.repos / "api", "branch", "--show-current"), "main")

    def test_existing_marker_is_compatible_and_marker_symlinks_are_rejected(self):
        workspace = self.tasks / "legacy"
        workspace.mkdir(parents=True)
        (workspace / manager.MARKER).write_text("mise-worktree-workspace-v1\n")
        self.wt("add", "legacy", "api")
        self.assert_worktree("legacy", "api")
        self.wt("remove", "legacy")
        workspace.mkdir()
        external = self.root / "external-marker"
        external.write_text(manager.VERSION + "\n")
        (workspace / manager.MARKER).symlink_to(external)
        self.wt("remove", "legacy", ok=False)
        self.assertTrue(external.exists())

    def test_environment_cannot_redirect_git_commands(self):
        env = dict(self.env, GIT_DIR=str(self.repos / "api/.git"),
                   GIT_WORK_TREE=str(self.repos / "api"), GIT_COMMON_DIR=str(self.repos / "api/.git"),
                   GIT_INDEX_FILE=str(self.root / "unrelated-index"))
        self.wt("create", "context", "auth", env=env)
        path = self.assert_worktree("context", "auth")
        self.assertEqual(self.git(path, "rev-parse", "--git-common-dir"), str(self.repos / "auth/.git"))
        self.assertFalse((self.root / "unrelated-index").exists())

    def test_failed_status_prevents_any_removal(self):
        self.wt("create", "preflight", "api", "auth")
        native_git = manager.git

        def failing_git(repo, *args, **kwargs):
            if Path(repo).name == "auth" and args[0] == "status":
                raise manager.WorkspaceError("Cannot read Git status")
            return native_git(repo, *args, **kwargs)

        with mock.patch.dict(os.environ, self.env, clear=True), mock.patch.object(manager, "git", side_effect=failing_git):
            with self.assertRaisesRegex(manager.WorkspaceError, "Nothing removed"):
                manager.remove(self.tasks / "preflight")
        self.assert_worktree("preflight", "api")
        self.assert_worktree("preflight", "auth")

    @unittest.skipUnless(shutil.which("mise"), "Mise is not installed")
    def test_mise_includes_argument_forwarding_interactive_io_and_errors(self):
        self.run_command(["mise", "run", "wt:create", "via-mise", "api", "front end"])
        self.assert_worktree("via-mise", "front end")
        self.run_command(["mise", "run", "wt:create", "../unsafe", "api"], ok=False)
        self.run_command(["mise", "run", "wt:add", "via-mise"], input="2\n")
        self.assert_worktree("via-mise", "auth")
        listing = self.run_command(["mise", "run", "wt:list"]).stdout
        self.assertIn("via-mise", listing)
        self.assertIn("## via-mise", self.run_command(["mise", "run", "wt:status", "via-mise"]).stdout)
        self.run_command(["mise", "run", "wt:remove", "via-mise"])
        self.assertFalse((self.tasks / "via-mise").exists())


if __name__ == "__main__":
    unittest.main()
