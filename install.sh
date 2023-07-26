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

setup_vim() {
  # https://github.com/wbthomason/packer.nvim#quickstart
  git clone --depth 1 https://github.com/wbthomason/packer.nvim\
    ~/.local/share/nvim/site/pack/packer/start/packer.nvim
  # You'll then have to run :PackerInstall from nvim
}

export -f setup_vim
