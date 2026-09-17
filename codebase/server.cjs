'use strict';
// Local preview only. Bind to loopback, and serve this folder without dependencies.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const files = { '/': 'index.html', '/index.html': 'index.html', '/styles.css': 'styles.css', '/app.js': 'app.js' };
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8' };
const server = http.createServer((req, res) => {
  const file = files[new URL(req.url, 'http://127.0.0.1').pathname];
  if (!file) { res.writeHead(404); res.end('Not found'); return; }
  fs.readFile(path.join(__dirname, file), (err, data) => {
    if (err) { res.writeHead(500); res.end('Cannot read preview file'); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(file)], 'Cache-Control': 'no-store' });
    res.end(data);
  });
});
server.on('error', err => { console.error('Cannot start local preview:', err.message); process.exitCode = 1; });
server.listen(4173, '127.0.0.1', () => console.log('Growup CP2: http://127.0.0.1:4173'));
