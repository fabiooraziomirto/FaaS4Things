const http = require('http');
const { exec } = require('child_process');
const fs = require('fs');
const crypto = require('crypto');

// Config
const PORT = 8888;
const NUCTL_PATH = 'nuctl';
const TEMP_DIR = '/tmp/nuclio-functions';
const SECRET_KEY = Buffer.from(process.env.SHARED_SECRET || '00'.repeat(32), 'hex');

// Crea dir tmp
if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}

// Funzione verifica firma
function verifySignature(req, body) {
    const signature = req.headers['x-signature'];
    if (!signature) return false;

    const payload = JSON.stringify(body, Object.keys(body).sort());
    const expected = crypto
        .createHmac('sha256', SECRET_KEY)
        .update(payload)
        .digest('hex');

    try {
        return crypto.timingSafeEqual(Buffer.from(signature, 'utf8'), Buffer.from(expected, 'utf8'));
    } catch {
        return false;
    }
}

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Signature');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    if ((req.url === '/deploy' || req.url === '/deploy-github') && req.method === 'POST') {
        let body = '';
        req.on('data', (chunk) => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);

                if (!verifySignature(req, data)) {
                    res.writeHead(403, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Firma non valida' }));
                    return;
                }

                if (req.url === '/deploy') {
                    deployFunction(data, res);
                } else {
                    deployFromGitHub(data, res);
                }
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'JSON non valido' }));
            }
        });
        return;
    }

    // altri endpoint (health, functions, ecc.) possono rimanere invariati
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint non trovato' }));
});

// Funzioni deploy originali (semplificate qui)
function deployFunction(data, res) {
    const { name, code, runtime = 'golang', buildCommand } = data;
    if (!name || !code) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Nome e codice richiesti' }));
        return;
    }
    const fileName = `${name}.${runtime === 'golang' ? 'go' : 'py'}`;
    const filePath = `${TEMP_DIR}/${fileName}`;
    fs.writeFileSync(filePath, code);
    let cmd = `${NUCTL_PATH} deploy ${name} --path "${filePath}" --runtime ${runtime} --platform local`;
    if (buildCommand) cmd += ` --build-command "${buildCommand}"`;
    exec(cmd, { timeout: 180000 }, (error, stdout, stderr) => {
        try { fs.unlinkSync(filePath); } catch {}
        if (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Deploy fallito', details: stderr || error.message }));
            return;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', output: stdout }));
    });
}

function deployFromGitHub(data, res) {
    const { name, githubUrl, runtime = 'golang', buildCommand, handler, platform = 'local' } = data;
    if (!name || !githubUrl) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Nome e URL GitHub richiesti' }));
        return;
    }
    let cmd = `${NUCTL_PATH} deploy ${name} --path "${githubUrl}" --runtime ${runtime} --platform ${platform}`;
    if (buildCommand) cmd += ` --build-command "${buildCommand}"`;
    if (handler) cmd += ` --handler "${handler}"`;
    exec(cmd, { timeout: 180000 }, (error, stdout, stderr) => {
        if (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Deploy GitHub fallito', details: stderr || error.message }));
            return;
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success', output: stdout }));
    });
}

server.listen(PORT, '127.0.0.1', () => {
    console.log(`Server Nuclio in ascolto su porta ${PORT}`);
});
