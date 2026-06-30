#!/usr/bin/env bash
set -euo pipefail

brew_formulae=(
  nvim
  fzf
  git
  tmux
  zsh
  awscli
  cmake
  jq
  gh
  rbenv
  ruby-build
  ripgrep
  wget
  opentofu
  openjdk@22
  uv
)

brew_casks=(
  claude-code
  codex
  font-symbols-only-nerd-font
)

for formula in "${brew_formulae[@]}"; do
  if ! brew list --formula "$formula" >/dev/null 2>&1; then
    brew install "$formula"
  fi
done

for cask in "${brew_casks[@]}"; do
  if ! brew list --cask "$cask" >/dev/null 2>&1; then
    brew install --cask "$cask"
  fi
done
