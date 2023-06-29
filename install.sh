#!/usr/bin/env bash

install_homebrew() {
  if ! command -v brew > /dev/null; then
    NONINTERACTIVE=1 /bin/bash -c "$(
      curl \
        --fail \
        --location \
        --show-error \
        --silent \
        https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh
    )"
  fi
}

install_applications() {
  brew install nvim fzf git tmux zsh awscli cmake jq 
}

main() {
  install_homebrew
  install_applications
}

main
