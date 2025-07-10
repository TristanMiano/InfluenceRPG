import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

// Determine __dirname in ESM context
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  plugins: [react()],
  // Serve files out of your static folder
  root: resolve(__dirname, 'src/server/static'),

  build: {
    // Output into dist/static relative to project root
    outDir: resolve(__dirname, 'dist/static'),
    emptyOutDir: true,

    // Emit manifest.json for template integration
    manifest: true,

    rollupOptions: {
      // All entry points to fingerprint
      input: {
        // JavaScript entries
        'chat': resolve(__dirname, 'src/server/static/js/chat.js'),
        'character_wizard': resolve(__dirname, 'src/server/static/js/character_wizard.jsx'),
        'create_account': resolve(__dirname, 'src/server/static/js/create_account.js'),
        'game_creation': resolve(__dirname, 'src/server/static/js/game_creation.js'),
        'lobby': resolve(__dirname, 'src/server/static/js/lobby.jsx'),
        'login': resolve(__dirname, 'src/server/static/js/login.js'),
        'universe_create': resolve(__dirname, 'src/server/static/js/universe_create.js'),
        'universes': resolve(__dirname, 'src/server/static/js/universes.jsx'),

        // CSS entries
        'style': resolve(__dirname, 'src/server/static/css/style.css'),
        'character_create_css': resolve(__dirname, 'src/server/static/css/character_create.css'),
        'game_creation_css': resolve(__dirname, 'src/server/static/css/game_creation.css'),
        'lobby_css': resolve(__dirname, 'src/server/static/css/lobby.css'),
        'login_css': resolve(__dirname, 'src/server/static/css/login.css'),
        'universes_css': resolve(__dirname, 'src/server/static/css/universes.css'),
      },
      output: {
        // Place all assets under 'assets/' with content hashes
        entryFileNames:   'assets/[name].[hash].js',
        chunkFileNames:   'assets/[name].[hash].js',
        assetFileNames:   'assets/[name].[hash].[ext]'
      }
    }
  }
})
