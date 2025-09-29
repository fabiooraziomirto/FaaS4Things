const http = require('http');
const crypto = require('crypto');

const MOCK_PORT = 8080;
const SECRET = process.env.FORWARD_SECRET || 'changeme';
const SIGNATURE_HEADER = 'x-signature';
const TIMESTAMP_HEADER = 'x-signature-timestamp';
const TIMESTAMP_TOLERANCE = 300;

function computeSignature(secret, bodyBuffer, timestamp) {
  const msg = Buffer.concat([bodyBuffer, Buffer.from(':' + timestamp)]);
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(msg);
  return 'sha256=' + hmac.digest('hex');
}

function safeCompare(a, b) {
  try {
    const bufA = Buffer.from(a);
    const bufB = Buffer.from(b);
    if (bufA.length !== bufB.length) return false;
    return crypto.timingSafeEqual(bufA, bufB);
  } catch {
    return false;
  }
}

function verifySignature(req, rawBuffer) {
  const sig = req.headers[SIGNATURE_HEADER];
  const ts = parseInt(req.headers[TIMESTAMP_HEADER], 10);
  if (!sig) {
    console.warn('[MOCK] Nessuna firma → modalità legacy');
    return true;
  }
  const now = Math.floor(Date.now() / 1000);
  if (!ts || Math.abs(now - ts) > TIMESTAMP_TOLERANCE) return false;
  const expected = computeSignature(SECRET, rawBuffer, ts);
  return safeCompare(expected, sig);
}

const server = http.createServer((req, res) => {
  if (req.method === 'POST') {
    let buffers = [];
    req.on('data', (chunk) => buffers.push(chunk));
    req.on('end', () => {
      const rawBuffer = Buffer.concat(buffers);
      if (!verifySignature(req, rawBuffer)) {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Firma non valida' }));
        return;
      }

      const body = JSON.parse(rawBuffer.toString());
      console.log('[MOCK] Richiesta ricevuta:', body);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        echo: body,
        mockResponse: 'Risposta di test dal mock server',
      }));
    });
  } else {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ message: 'Mock server attivo' }));
  }
});

server.listen(MOCK_PORT, () => {
  console.log(`✅ Mock server in ascolto su http://localhost:${MOCK_PORT}`);
});
