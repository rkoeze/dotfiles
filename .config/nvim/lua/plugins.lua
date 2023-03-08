return require('packer').startup(function(use)
  use 'wbthomason/packer.nvim'

  use 'w0rp/ale'

  use 'mattn/emmet-vim'

  use 'tpope/vim-unimpaired'

  use {
    'hrsh7th/nvim-cmp',
    requires = {{'hrsh7th/cmp-buffer'}}
  }

  require('cmp').setup({
    sources = {
      { name = 'buffer' },
    },
  })

  use {
    'nvim-telescope/telescope.nvim', tag = '0.1.1',
    requires = { {'nvim-lua/plenary.nvim'} }
  }
end)

