#!/usr/bin/env bash

pull_down_dotfiles() {
  alias dotfiles='/usr/bin/git --git-dir=$HOME/.dtcg/ --work-tree=$HOME'
  git clone --bare https://github.com/rkoeze/dotfiles.git $HOME/.dtcg
  dotfiles checkout
  dotfiles config --local status.showUntrackedFiles no
}

install_homebrew() {
  if ! command -v brew > /dev/null; then
    /bin/bash -c "$(
    curl \
      --fail \
      --location \
      --show-error \
      --silent \
      https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh
          )"
  fi
}

export -f install_homebrew

install_applications() {
  brew install nvim fzf git tmux zsh awscli cmake jq gh rbenv ruby-build ripgrep wget opentofu openjdk@22 uv
}

export -f install_applications

install_cask_applications() {
  brew install --cask codex claude-code font-symbols-only-nerd-font
}

export -f install_cask_applications

auth_github() {
  gh auth login
}

export -f auth_github
