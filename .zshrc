# Set PATH, MANPATH, etc., for Homebrew.
eval "$(/opt/homebrew/bin/brew shellenv)"
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dtcg/ --work-tree=$HOME'

# we always want nvim
alias vim=nvim
alias vi=nvim
alias view=nvim

# some ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# git aliases
alias gcm='git commit --verbose'
alias gss='git status'
alias gco='git checkout'
alias gack='git log --pretty="%an <%ae>" | sort -u | fzf | xargs -I "{}" commit --no-edit --amend --trailer "Co-authored-by: {}"'

export EDITOR=nvim

# binds all keys to the standard vi-like bindings.
bindkey -e

# Terminal prompt that includes git branch
autoload -Uz compinit && compinit
autoload -Uz add-zsh-hook
autoload -Uz vcs_info

add-zsh-hook precmd vcs_info

zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:*' formats " %F{cyan}%c%u(%b)%f"
zstyle ':vcs_info:*' actionformats " %F{cyan}%c%u(%b)%f %a"
zstyle ':vcs_info:*' stagedstr "%F{green}"
zstyle ':vcs_info:*' unstagedstr "%F{red}"
zstyle ':vcs_info:*' check-for-changes true

zstyle ':vcs_info:git*+set-message:*' hooks git-untracked

+vi-git-untracked() {
  if git --no-optional-locks status --porcelain 2> /dev/null | grep -q "^??"; then
    hook_com[staged]+="%F{red}"
  fi
}

setopt PROMPT_SUBST
export PROMPT='%n:%1~$vcs_info_msg_0_ %# '

autoload -U +X bashcompinit && bashcompinit

export PATH=/opt/homebrew/opt/postgresql@15/bin:$PATH


export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
