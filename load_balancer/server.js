const http = require('http');
const { exec } = require('child_process');
const fs = require('fs');
const crypto = require('crypto');

// Configurazione
const PORT = 8888;
const NUCTL_PATH = 'nuctl';
const TEMP_DIR = '/tmp/nuclio-functions';

// Sicurezza
const SECRET = process.env.IOT_SECRET || 'changeme';
const SIGNATURE_HEADER = 'x-signature';
const TIMESTAMP_HEADER = 'x-signature-timestamp';
const TIMESTAMP_TOLERANCE = 300; // secondi

if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}

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
    } catch (e) {
        return false;
    }
}

function verifyRequestSignature(req, rawBuffer) {
    const sigHeader = req.headers[SIGNATURE_HEADER];
    const tsHeader = req.headers[TIMESTAMP_HEADER];

    if (!sigHeader) {
        console.warn("Signature assente -> modalità legacy");
        return true; // compatibilità
    }

    const ts = parseInt(tsHeader, 10);
    const now = Math.floor(Date.now() / 1000);
    if (!ts || Math.abs(now - ts) > TIMESTAMP_TOLERANCE) {
        return false;
    }

    const expected = computeSignature(SECRET, rawBuffer, ts);
    return safeCompare(expected, sigHeader);
}

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Signature, X-Signature-Timestamp');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    let bodyBuffers = [];
    req.on('data', (chunk) => bodyBuffers.push(chunk));
    req.on('end', () => {
        const rawBuffer = Buffer.concat(bodyBuffers);
        const rawString = rawBuffer.toString();

        // Verifica firma
        if (!verifyRequestSignature(req, rawBuffer)) {
            res.writeHead(401, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Signature non valida' }));
            return;
        }

        // Routing
        if (req.url === '/health' && req.method === 'GET') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'healthy', server: 'nuclio-deploy-server' }));
            return;
        }

        if (req.url === '/deploy' && req.method === 'POST') {
            try {
                const functionData = JSON.parse(rawString);
                deployFunction(functionData, res);
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'JSON non valido' }));
            }
            return;
        }

        if (req.url === '/deploy-github' && req.method === 'POST') {
            try {
                const githubData = JSON.parse(rawString);
                deployFromGitHub(githubData, res);
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'JSON non valido' }));
            }
            return;
        }

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Endpoint non trovato' }));
    });
});

// Funzioni deploy
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
        res.end(JSON.stringify({ status: 'success', message: `Funzione ${name} deployata`, output: stdout }));
    });
}

function deployFromGitHub(data, res) {
    const { name, githubUrl, runtime = 'golang', subPath = '', buildCommand, handler, platform = 'local' } = data;

    if (!name || !githubUrl) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Nome e URL GitHub sono richiesti' }));
        return;
    }

    console.log(`Deploy da GitHub: ${name} - ${githubUrl}`);
    console.log(`Parametri ricevuti:`, JSON.stringify(data, null, 2));

    // Costruisci il path completo se c'è un subPath
    const fullGithubPath = subPath ? `${githubUrl}/${subPath}` : githubUrl;

    // Costruisci il comando base
    let cmd = `${NUCTL_PATH} deploy ${name} --path "${fullGithubPath}" --runtime ${runtime} --platform ${platform}`;

    // Aggiungi build-command se specificato
    if (buildCommand) {
        cmd += ` --build-command "${buildCommand}"`;
    }

    // Aggiungi handler se specificato
    if (handler) {
        cmd += ` --handler "${handler}"`;
    }

    console.log(`Esecuzione: ${cmd}`);

    exec(cmd, { timeout: 180000 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Errore deploy da GitHub: ${error.message}`);
            console.error(`Stderr: ${stderr}`);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                error: 'Deploy da GitHub fallito',
                details: error.message,
                stderr: stderr
            }));
            return;
        }

        console.log(`Deploy da GitHub completato: ${name}`);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'success',
            message: `Funzione ${name} deployata da GitHub con successo`,
            source: githubUrl,
            buildCommand: buildCommand || 'none',
            output: stdout
        }));
    });
}

server.listen(PORT, '127.0.0.1', () => {
    console.log(`Server IoT in ascolto su porta ${PORT}`);
});
