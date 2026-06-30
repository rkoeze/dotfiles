#!/usr/bin/env bash

pull_down_dotfiles() {
  if [ ! -d "$HOME/.dtcg" ]; then
    git clone --bare https://github.com/rkoeze/dotfiles.git "$HOME/.dtcg"
  fi

  /usr/bin/git --git-dir="$HOME/.dtcg/" --work-tree="$HOME" checkout
  /usr/bin/git --git-dir="$HOME/.dtcg/" --work-tree="$HOME" config --local status.showUntrackedFiles no
}

export -f pull_down_dotfiles

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

install_mise() {
  if ! command -v mise > /dev/null; then
    curl https://mise.run | sh
  fi
}

export -f install_mise
