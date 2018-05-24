set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'VundleVim/Vundle.vim'

Plugin 'Raimondi/delimitMate'
let delimitMate_expand_cr=1

Plugin 'Valloric/YouCompleteMe'
let g:ycm_autoclose_preview_window_after_completion = 1

Plugin 'ternjs/tern_for_vim'

Plugin 'wincent/command-t'
" Open files with <leader>f
map <leader>f :CommandTFlush<cr>\|:CommandT<cr>
" Open files, limited to the directory of the current file, with <leader>gf
" This requires the %% mapping found below.
map <leader>gf :CommandTFlush<cr>\|:CommandT %%<cr>

Plugin 'mattn/emmet-vim'

Plugin 'w0rp/ale'
map <leader>c :ALEToggle<CR>

Plugin 'tpope/vim-unimpaired'

call vundle#end()

set nocompatible

set hidden

filetype off

syntax on

set path+=**

set wildmenu

filetype plugin indent on 

set hlsearch

set nobackup

set noswapfile

cnoremap %% <C-R>=expand('%:h').'/'<cr>
map <leader>e :edit %%

map <leader>t :tabnew<cr>

set winwidth=84
" We have to have a winheight bigger than we want to set winminheight. But if
" we set winheight to be huge before winminheight, the winminheight set will
" fail.
set winheight=5
set winminheight=5
set winheight=999

set number
set showmatch
set tabstop=2 
set softtabstop=2
set expandtab 
set shiftwidth=2 
set smarttab
set autoindent
set smartindent
set lazyredraw
set regexpengine=1
set backspace=2 

set colorcolumn=80

" Always show tab bar at the top
set showtabline=2
set winwidth=79

" make searches case-sensitive only if they contain upper-case characters
set ignorecase smartcase

" use emacs-style tab completion when selecting files, etc
set wildmode=longest,list

" make tab completion for files/buffers act like bash
set wildmenu

" If a file is changed outside of vim, automatically reload it without asking
set autoread

set statusline=%<%f\ (%{&ft})\ %-4(%m%)%=%-19(%3l,%02c%03V%)

autocmd Filetype java setlocal shiftwidth=4 tabstop=4

set tags=tags

let g:ruby_path = system('echo $HOME/.rbenv/shims')
