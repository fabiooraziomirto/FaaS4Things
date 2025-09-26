const http = require('http');

const MOCK_PORT = 8080;

const server = http.createServer((req, res) => {
  if (req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => (body += chunk.toString()));
    req.on('end', () => {
      console.log('Richiesta ricevuta:', body);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          success: true,
          echo: JSON.parse(body),
          mockResponse: 'Risposta di test dal mock server',
        })
      );
    });
  } else {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ message: 'Mock server attivo' }));
  }
});

server.listen(MOCK_PORT, () => {
  console.log(`Mock server in ascolto su http://localhost:${MOCK_PORT}`);
});
