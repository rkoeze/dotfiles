return require('packer').startup(function(use)
  use 'wbthomason/packer.nvim'

  use 'mattn/emmet-vim'

  use 'tpope/vim-unimpaired'

  use {
    'hrsh7th/nvim-cmp',
    requires = {{'hrsh7th/cmp-buffer'}}
  }

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

  use {
    'nvim-telescope/telescope.nvim', tag = '0.1.1',
    requires = { {'nvim-lua/plenary.nvim'} }
  }

  require('telescope').setup{
    pickers = {
      find_files = {
        theme = "dropdown",
      }
    }
  }

  require("tokyonight").setup({
    style = "night",
    on_highlights = function(hl, c)
      hl.TabLine = {
        fg = '#c1c7e3',
      }
    end,
  })

  use 'folke/tokyonight.nvim'

  use 'dense-analysis/ale'
end)
