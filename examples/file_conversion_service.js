const http = require('http');
const port = Number(process.env.PORT || 9000);

function sendJson(res, status, payload) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  res.end(JSON.stringify(payload));
}

const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') return sendJson(res, 204, {});
  if (req.url === '/health' && req.method === 'GET') return sendJson(res, 200, { status: 'ok', service: 'text-case-converter' });
  if (req.url === '/invoke' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => body += chunk);
    req.on('end', () => {
      try {
        const parsed = body ? JSON.parse(body) : {};
        const text = String(parsed.text || '');
        const operation = String(parsed.operation || 'uppercase').toLowerCase();
        const result = operation === 'lowercase' ? text.toLowerCase() : text.toUpperCase();
        const bytes = Buffer.byteLength(result, 'utf8');
        sendJson(res, 200, { operation, input: text, output: result, bytes, converter: 'agents-talk-demo' });
      } catch (err) {
        sendJson(res, 400, { error: 'invalid JSON', detail: err.message });
      }
    });
    return;
  }
  sendJson(res, 404, { error: 'not found' });
});

server.listen(port, '0.0.0.0', () => console.log(`file-conversion-service listening on ${port}`));
