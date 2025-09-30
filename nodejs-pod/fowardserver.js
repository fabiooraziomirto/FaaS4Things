const http = require('http');
const https = require('https');
const url = require('url');
const crypto = require('crypto');

const PORT = 3000;
const FORWARD_SECRET = process.env.FORWARD_SECRET || 'forward_secret_123';
const TIMESTAMP_TOLERANCE = 300; // 5 minuti

// Mapping delle variabili ai server Monk
const TARGET_SERVERS = {
  server1: 'http://localhost:8080',
  // server2: 'http://192.168.1.101:8080',
  // server3: 'http://192.168.1.102:8080',
};

// 🔐 Funzione per calcolare la firma attesa
function computeSignature(secret, rawBody, timestamp) {
  const msg = `${rawBody}:${timestamp}`;
  const sig = crypto.createHmac('sha256', secret).update(msg).digest('hex');
  return `sha256=${sig}`;
}

// 🧠 Verifica firma HMAC
function verifySignature(req, rawBuffer) {
  const signature = req.headers['x-signature'];
  const timestamp = req.headers['x-signature-timestamp'];

  if (!signature || !timestamp) {
    console.warn('[FORWARD] Nessuna firma presente → rifiutato');
    return false;
  }

  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp, 10)) > TIMESTAMP_TOLERANCE) {
    console.warn('[FORWARD] Timestamp non valido o scaduto');
    return false;
  }

  const expected = computeSignature(FORWARD_SECRET, rawBuffer.toString(), timestamp);
  const sigBuf = Buffer.from(signature);
  const expBuf = Buffer.from(expected);
  if (sigBuf.length !== expBuf.length || !crypto.timingSafeEqual(sigBuf, expBuf)) {
    console.warn('[FORWARD] Firma non valida');
    return false;
  }

  return true;
}

// 📡 Funzione per inoltrare la richiesta al Monk
function makeRequest(targetUrl, data) {
  return new Promise((resolve, reject) => {
    const parsedUrl = url.parse(targetUrl);
    const isHttps = parsedUrl.protocol === 'https:';
    const client = isHttps ? https : http;
    const postData = JSON.stringify(data);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (isHttps ? 443 : 80),
      path: parsedUrl.path || '/',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'X-Forwarded-From': 'forward-server',
      },
    };

    const req = client.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => (responseData += chunk));
      res.on('end', () => {
        try {
          resolve({ statusCode: res.statusCode, data: JSON.parse(responseData) });
        } catch {
          resolve({ statusCode: res.statusCode, data: responseData });
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(postData);
    req.end();
  });
}

// 🚀 Server HTTP
const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Signature, X-Signature-Timestamp');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === 'POST' && req.url === '/forward') {
    let buffers = [];
    req.on('data', (chunk) => buffers.push(chunk));
    req.on('end', async () => {
      const rawBuffer = Buffer.concat(buffers);

      if (!verifySignature(req, rawBuffer)) {
        res.writeHead(401, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Firma non valida' }));
        return;
      }

      let requestData;
      try {
        requestData = JSON.parse(rawBuffer.toString());
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'JSON non valido', message: err.message }));
        return;
      }

      const { variable, instruction } = requestData;
      if (!variable || !instruction) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          error: 'Parametri mancanti',
          message: 'Sono richiesti i parametri "variable" e "instruction"',
        }));
        return;
      }

      const targetUrl = TARGET_SERVERS[variable];
      if (!targetUrl) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          error: 'Variabile non valida',
          message: `La variabile "${variable}" non corrisponde a nessun server configurato`,
          availableServers: Object.keys(TARGET_SERVERS),
        }));
        return;
      }

      console.log(`[FORWARD] Forwarding instruction "${instruction}" to ${targetUrl}`);

      try {
        const response = await makeRequest(targetUrl, requestData);
        res.writeHead(response.statusCode, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          forwardedTo: targetUrl,
          data: response.data,
        }));
      } catch (error) {
        console.error('[FORWARD] Errore inoltro →', error.message);
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Errore inoltro', message: error.message }));
      }
    });
  } else if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'OK',
      timestamp: new Date().toISOString(),
      availableServers: Object.keys(TARGET_SERVERS),
    }));
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      error: 'Endpoint non trovato',
      message: 'Usa POST /forward per forwardare le richieste',
    }));
  }
});

server.listen(PORT, () => {
  console.log(`🚀 Forward server attivo su http://localhost:${PORT}`);
  console.log('Server Monk configurati:', TARGET_SERVERS);
});
