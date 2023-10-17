local lazypath = vim.fn.stdpath 'data' .. '/lazy/lazy.nvim'
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system {
    'git',
    'clone',
    '--filter=blob:none',
    'https://github.com/folke/lazy.nvim.git',
    '--branch=stable', -- latest stable release
    lazypath,
  }
end
vim.opt.rtp:prepend(lazypath)

require('lazy').setup({
  {
    'hrsh7th/nvim-cmp',
    dependencies = {'hrsh7th/cmp-buffer'}
  },

  {
    'nvim-telescope/telescope.nvim', branch = '0.1.x',
    dependencies = {'nvim-lua/plenary.nvim'}
  },

  'folke/tokyonight.nvim',

  'dense-analysis/ale',

  'nvim-treesitter/nvim-treesitter'
})

-- 'hrsh7th/nvim-cmp'
local cmp = require'cmp'
cmp.setup({
  mapping = cmp.mapping.preset.insert({
    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
    ['<C-f>'] = cmp.mapping.scroll_docs(4),
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<C-e>'] = cmp.mapping.abort(),
    ['<CR>'] = cmp.mapping.confirm({ select = true }), -- Accept currently selected item. Set `select` to `false` to only confirm explicitly selected items.
    ['<Tab>'] = cmp.mapping(cmp.mapping.select_next_item(), { 'i', 's' }),
    ['<S-Tab>'] = cmp.mapping(cmp.mapping.select_prev_item(), { 'i', 's' })
  }),
  sources = cmp.config.sources({}, {
    { name = 'buffer' },
  })
})

-- 'nvim-telescope/telescope.nvim'
require('telescope').setup{
  pickers = {
    find_files = {
      theme = "dropdown",
    }
  }
}

vim.api.nvim_set_keymap('n', '<leader>ff', '<cmd>Telescope find_files<cr>', {noremap = true, silent = true})
vim.api.nvim_set_keymap('n', '<leader>fg', '<cmd>Telescope live_grep<cr>', {noremap = true, silent = true})
vim.api.nvim_set_keymap('n', '<leader>fb', '<cmd>Telescope buffers<cr>', {noremap = true, silent = true})
vim.api.nvim_set_keymap('n', '<leader>fh', '<cmd>Telescope help_tags<cr>', {noremap = true, silent = true})

-- 'folke/tokyonight.nvim',
require("tokyonight").setup({
  style = "night",
  on_highlights = function(hl, c)
    hl.TabLine = {
      fg = '#c1c7e3',
    }
  end,
})

vim.cmd("colorscheme tokyonight")
-- 'dense-analysis/ale',
vim.g.ale_linters = {
  python = {"flake8"}
} 

-- explicitly turn off compatability with good old vi
vim.o.compatible=false

-- allow unsaved work not displayed on screen
vim.o.hidden=true

-- causes all searches to be highlighted
vim.cmd("set hlsearch")

-- immediately delete backup file on succesful write
vim.o.backup=false

-- don't use swap files
vim.o.noswapfile=false

-- map %% to expland filepath (used 1 line below)
vim.cmd("cnoremap %% <C-R>=expand('%:h').'/'<cr>")
vim.api.nvim_set_keymap('n', '<leader>e', ':edit %%', {noremap=true, silent=true})
vim.api.nvim_set_keymap('n', '<leader>t', ':tabnew<cr>', {noremap=true, silent=true})
vim.api.nvim_set_keymap('n', '<leader>o', ':Ex<cr>', {noremap=true, silent=true})
vim.api.nvim_set_keymap('n', '<leader>n', ':nohlsearch<cr>', {noremap=true, silent=true})

-- show line numbers
vim.o.number=true

-- when a bracket is inserted, briefly jump to the matching one.  T
vim.o.showmatch=true
vim.o.autoindent=true
vim.o.smartindent=true
vim.o.lazyredraw=true
vim.o.regexpengine=1
vim.o.backspace=2 

-- tab stuff
vim.o.tabstop=2 
vim.o.softtabstop=2
vim.o.expandtab=true
vim.o.shiftwidth=2 
vim.o.smarttab=true

-- Always show tab bar at the top
vim.o.showtabline=2

-- make searches case-sensitive only if they contain upper-case characters
vim.o.ignorecase=true
vim.o.smartcase=true

-- use emacs-style tab completion when selecting files, etc
vim.o.wildmode="longest,list"

-- make tab completion for files/buffers act like bash
vim.o.wildmenu=true

-- If a file is changed outside of vim, automatically reload it without asking
vim.o.autoread=true

-- Use new regular expression engine
vim.o.re=0

-- File type specific commands
-- Java
vim.cmd[[autocmd Filetype java setlocal shiftwidth=4 tabstop=4]]
-- Python
vim.cmd[[autocmd FileType python setlocal tabstop=8 shiftwidth=4 softtabstop=4]]
vim.cmd[[autocmd FileType python set colorcolumn=88]]

vim.keymap.set("n", "=", [[<cmd>vertical resize +5<cr>]]) -- make the window biger vertically
vim.keymap.set("n", "-", [[<cmd>vertical resize -5<cr>]]) -- make the window smaller vertically
vim.keymap.set("n", "+", [[<cmd>horizontal resize +2<cr>]]) -- make the window bigger horizontally by pressing shift and =
vim.keymap.set("n", "_", [[<cmd>horizontal resize -2<cr>]]) -- make the window smaller horizontally by pressing shift and -
