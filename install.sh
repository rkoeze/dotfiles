#!/usr/bin/env bash

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
  brew install nvim fzf git tmux zsh awscli cmake jq gh
}

export -f install_applications

auth_github() {
  gh auth login
}

export -f auth_github
