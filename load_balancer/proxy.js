const http = require('http');
 
// Configurazione
const PROXY_PORT = 8000;
const TARGET_HOST = '127.0.0.1';
const TARGET_PORT = 8888;
 
// Server proxy
const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
 
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
 
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
 
    // Health check del proxy
    if (req.url === '/health' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            proxy: 'running',
            target: `${TARGET_HOST}:${TARGET_PORT}`
        }));
        return;
    }
 
    // Inoltra tutte le altre richieste al server Nuclio
    const options = {
        hostname: TARGET_HOST,
        port: TARGET_PORT,
        path: req.url,
        method: req.method,
        headers: req.headers
    };
 
    const proxyReq = http.request(options, (proxyRes) => {
        // Copia headers della risposta
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        // Inoltra la risposta
        proxyRes.pipe(res);
    });
 
    proxyReq.on('error', (err) => {
        console.error(`Errore proxy: ${err.message}`);
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Errore connessione al server Nuclio' }));
    });
 
    // Inoltra il body della richiesta
    req.pipe(proxyReq);
});
 
server.listen(PROXY_PORT, '0.0.0.0', () => {
    console.log(`Proxy in ascolto su porta ${PROXY_PORT}`);
    console.log(`Inoltra richieste a ${TARGET_HOST}:${TARGET_PORT}`);
});