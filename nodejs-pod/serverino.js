const http = require('http');
const https = require('https');
const url = require('url');

const PORT = 3000;

// Mapping delle variabili agli indirizzi IP di destinazione
const TARGET_SERVERS = {
  server1: 'http://localhost:8080',
// server2: 'http://192.168.1.101:8080',
// server3: 'http://192.168.1.102:8080',
// database: 'http://10.0.0.50:5000',
// api: 'http://10.0.0.51:3000',
};

// Funzione per fare HTTP request
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

      res.on('data', (chunk) => {
        responseData += chunk;
      });

      res.on('end', () => {
        try {
          const jsonData = JSON.parse(responseData);
          resolve({ statusCode: res.statusCode, data: jsonData });
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: responseData });
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.write(postData);
    req.end();
  });
}

// Server HTTP
const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url, true);

  if (req.method === 'POST' && parsedUrl.pathname === '/forward') {
    let body = '';

    req.on('data', (chunk) => {
      body += chunk.toString();
    });

    req.on('end', async () => {
      try {
        const requestData = JSON.parse(body);
        const { variable, function: functionParam } = requestData;

        // Validazione parametri
        if (!variable || !functionParam) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({
              error: 'Parametri mancanti',
              message:
                'Sono richiesti i parametri "variable" e "function"',
            })
          );
          return;
        }

        // Controllo server di destinazione
        const targetUrl = TARGET_SERVERS[variable];
        if (!targetUrl) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({
              error: 'Variabile non valida',
              message: `La variabile "${variable}" non corrisponde a nessun server configurato`,
              availableServers: Object.keys(TARGET_SERVERS),
            })
          );
          return;
        }

        console.log(`Forwarding request to ${targetUrl}`);
        console.log(`Variable: ${variable}, Function: ${functionParam}`);

        // Forward della richiesta
        try {
          const response = await makeRequest(targetUrl, {
            variable: variable,
            function: functionParam,
          });

          res.writeHead(response.statusCode, {
            'Content-Type': 'application/json',
          });
          res.end(
            JSON.stringify({
              success: true,
              forwardedTo: targetUrl,
              data: response.data,
            })
          );
        } catch (error) {
          console.error('Errore nel forward:', error.message);

          let statusCode = 500;
          let errorMessage = 'Errore interno del server';

          if (error.code === 'ECONNREFUSED') {
            statusCode = 503;
            errorMessage = 'Server di destinazione non raggiungibile';
          } else if (error.code === 'ENOTFOUND') {
            statusCode = 502;
            errorMessage = 'Server di destinazione non trovato';
          } else if (error.message === 'Request timeout') {
            statusCode = 504;
            errorMessage =
              'Timeout nella connessione al server di destinazione';
          }

          res.writeHead(statusCode, { 'Content-Type': 'application/json' });
          res.end(
            JSON.stringify({
              error: errorMessage,
              message: error.message,
            })
          );
        }
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            error: 'JSON non valido',
            message: error.message,
          })
        );
      }
    });
  } else if (req.method === 'GET' && parsedUrl.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        status: 'OK',
        timestamp: new Date().toISOString(),
        availableServers: Object.keys(TARGET_SERVERS),
      })
    );
  } else if (req.method === 'GET' && parsedUrl.pathname === '/config') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        targetServers: TARGET_SERVERS,
        description:
          'Mapping delle variabili agli indirizzi IP di destinazione',
      })
    );
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        error: 'Endpoint non trovato',
        message: 'Usa POST /forward per forwardare le richieste',
      })
    );
  }
});

server.listen(PORT, () => {
  console.log(`Server REST avviato sulla porta ${PORT}`);
  console.log('Endpoint disponibili:');
  console.log(' POST /forward - Forward delle richieste');
  console.log(' GET /health - Stato del server');
  console.log(' GET /config - Configurazione server');
  console.log('\nServer configurati:');

  Object.entries(TARGET_SERVERS).forEach(([key, url]) => {
    console.log(` ${key} -> ${url}`);
  });
});

process.on('SIGINT', () => {
  console.log('\nChiusura del server...');
  server.close(() => {
    console.log('Server chiuso.');
    process.exit(0);
  });
});
