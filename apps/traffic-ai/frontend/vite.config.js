import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import fs from 'node:fs';

function legacyTraficFrontend() {
  const legacyDir = path.resolve(__dirname, '../../legacy-sumo/frontend');
  const legacyFiles = new Set(['index.html', 'junction.html']);

  return {
    name: 'legacy-trafic-frontend',
    buildStart() {
      // For `vite build`, copy the legacy HTML into Vite's `public/legacy/`
      // so `/legacy/index.html` works without dev middleware.
      const publicLegacyDir = path.resolve(__dirname, 'public/legacy');
      fs.mkdirSync(publicLegacyDir, { recursive: true });
      for (const file of legacyFiles) {
        const src = path.resolve(path.join(legacyDir, file));
        const dest = path.resolve(path.join(publicLegacyDir, file));
        fs.copyFileSync(src, dest);
      }
    },
    configureServer(server) {
      server.middlewares.use('/legacy', (req, res, next) => {
        const urlPath = (req.url || '').split('?')[0] || '';
        const relPath = urlPath.replace(/^\/+/, '');

        if (!legacyFiles.has(relPath)) return next();

        const requestedPath = path.resolve(path.join(legacyDir, relPath));
        if (!requestedPath.startsWith(legacyDir)) return next(); // basic traversal guard

        fs.readFile(requestedPath, 'utf8', (err, data) => {
          if (err) return next();
          res.statusCode = 200;
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.end(data);
        });
      });
    }
  };
}

export default defineConfig({
  plugins: [react(), legacyTraficFrontend()],
  server: {
    port: 5173
  }
});
