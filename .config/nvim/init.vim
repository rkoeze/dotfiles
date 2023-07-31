lua require('plugins')

set nocompatible

set hidden

filetype off

set path+=**

set wildmenu

filetype plugin indent on 

syntax on

set hlsearch

set nobackup

set noswapfile

cnoremap %% <C-R>=expand('%:h').'/'<cr>
map <leader>e :edit %%

map <leader>t :tabnew<cr>

map <leader>o :Ex<cr>

map <leader>n :nohlsearch<cr>

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

" set colorcolumn=80

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

" Use new regular expression engine
set re=0

set statusline=%<%f\ (%{&ft})\ %-4(%m%)%=%-19(%3l,%02c%03V%)

autocmd Filetype java setlocal shiftwidth=4 tabstop=4
autocmd FileType python setlocal tabstop=8 shiftwidth=4 softtabstop=4

" Telescope
nnoremap <leader>ff <cmd>Telescope find_files<cr>
nnoremap <leader>fg <cmd>Telescope live_grep<cr>
nnoremap <leader>fb <cmd>Telescope buffers<cr>
nnoremap <leader>fh <cmd>Telescope help_tags<cr>

" Tokyonight
colorscheme tokyonight
