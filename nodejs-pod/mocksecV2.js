const http = require('http');
const crypto = require('crypto');

const PORT = 8080;

// La stessa chiave usata dal forward server e dalle funzioni Nuclio
const SECRET = process.env.FORWARD_SECRET || 'forward_secret_123';

const SIGNATURE_HEADER = 'x-signature';
const TIMESTAMP_HEADER = 'x-signature-timestamp';
const TIMESTAMP_TOLERANCE = 300; // 5 minuti

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
    console.warn('[MONK] Nessuna firma → modalità legacy');
    return true;
  }

  const now = Math.floor(Date.now() / 1000);
  if (!ts || Math.abs(now - ts) > TIMESTAMP_TOLERANCE) {
    console.warn('[MONK] Timestamp non valido o scaduto');
    return false;
  }

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

      let body;
      try {
        body = JSON.parse(rawBuffer.toString());
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'JSON non valido' }));
        return;
      }

      console.log('[MONK] Richiesta ricevuta:', body);

      // Logica sulle istruzioni
      let result;
      switch (body.instruction) {
        case 'istruzione1':
          // Esempio: esegui azione A
          result = { success: true, message: 'Istruzione 1 eseguita con successo', payload: body.payload };
          break;

        case 'istruzione2':
          // Esempio: esegui azione B
          result = { success: true, message: 'Istruzione 2 eseguita con successo', extra: 'Azione B completata' };
          break;

        default:
          result = { success: false, message: `Istruzione sconosciuta: ${body.instruction}` };
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    });
  } else {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ message: 'Monk server attivo' }));
  }
});

server.listen(PORT, () => {
  console.log(`✅ Monk server in ascolto su http://localhost:${PORT}`);
});
