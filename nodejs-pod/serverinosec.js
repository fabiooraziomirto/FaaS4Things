const http = require('http');
const https = require('https');
const url = require('url');
const crypto = require('crypto');

const PORT = 3000;
const SECRET = process.env.FORWARD_SECRET || 'changeme';
const SIGNATURE_HEADER = 'x-signature';
const TIMESTAMP_HEADER = 'x-signature-timestamp';
const TIMESTAMP_TOLERANCE = 300; // 5 minuti

const TARGET_SERVERS = {
  server1: 'http://localhost:8080',
};

// --- FIRMA E VERIFICA ---

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
  const sigHeader = req.headers[SIGNATURE_HEADER];
  const tsHeader = req.headers[TIMESTAMP_HEADER];

  if (!sigHeader) {
    console.warn('[SIGN] Nessuna firma nella richiesta → modalità legacy');
    return true;
  }

  const ts = parseInt(tsHeader, 10);
  const now = Math.floor(Date.now() / 1000);
  if (!ts || Math.abs(now - ts) > TIMESTAMP_TOLERANCE) {
    console.warn('[SIGN] Timestamp non valido o scaduto');
    return false;
  }

  const expected = computeSignature(SECRET, rawBuffer, ts);
  return safeCompare(expected, sigHeader);
}

function signRequest(bodyBuffer) {
  const ts = Math.floor(Date.now() / 1000);
  const sig = computeSignature(SECRET, bodyBuffer, ts);
  return {
    [SIGNATURE_HEADER]: sig,
    [TIMESTAMP_HEADER]: ts.toString(),
  };
}

// --- FUNZIONE FORWARD ---

function makeRequest(targetUrl, data) {
  return new Promise((resolve, reject) => {
    const parsedUrl = url.parse(targetUrl);
    const isHttps = parsedUrl.protocol === 'https:';
    const client = isHttps ? https : http;
    const postData = Buffer.from(JSON.stringify(data));

    const extraHeaders = signRequest(postData);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.path || '/',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'X-Forwarded-From': 'forward-server',
        ...extraHeaders
      },
    };

    const req = client.request(options, (res) => {
      let responseData = '';

      res.on('data', (chunk) => {
        responseData += chunk;
      });

      res.on('end', () => {
        try {
          const jsonData = JSON.parse(responseData);
          resolve({ statusCode: res.statusCode, data: jsonData });
        } catch {
          resolve({ statusCode: res.statusCode, data: responseData });
        }
      });
    });

    req.on('error', (error) => reject(error));
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(postData);
    req.end();
  });
}

// --- SERVER ---

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Signature, X-Signature-Timestamp');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url, true);

  if (req.method === 'POST' && parsedUrl.pathname === '/forward') {
    let buffers = [];
    req.on('data', (chunk) => buffers.push(chunk));
    req.on('end', async () => {
      const rawBuffer = Buffer.concat(buffers);

      if (!verifySignature(req, rawBuffer)) {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Firma non valida' }));
        return;
      }

      try {
        const requestData = JSON.parse(rawBuffer.toString());
        const { variable, function: functionParam } = requestData;

        if (!variable || !functionParam) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Parametri mancanti' }));
          return;
        }

        const targetUrl = TARGET_SERVERS[variable];
        if (!targetUrl) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Variabile non valida', availableServers: Object.keys(TARGET_SERVERS) }));
          return;
        }

        console.log(`[FORWARD] → ${targetUrl}`);
        const response = await makeRequest(targetUrl, requestData);

        res.writeHead(response.statusCode, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          forwardedTo: targetUrl,
          data: response.data,
        }));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'JSON non valido', message: error.message }));
      }
    });
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint non trovato' }));
  }
});

server.listen(PORT, () => {
  console.log(`✅ Forward server in ascolto su http://localhost:${PORT}`);
});
