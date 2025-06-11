const http = require('http');
const { exec } = require('child_process');
const fs = require('fs');
 
// Configurazione
const PORT = 8888;
const NUCTL_PATH = 'nuctl';
const TEMP_DIR = '/tmp/nuclio-functions';
 
// Crea directory temporanea
if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}
 
const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
 
    // CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
 
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
 
    // Health check
    if (req.url === '/health' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            server: 'nuclio-deploy-server'
        }));
        return;
    }
 
    // Deploy da codice inline
    if (req.url === '/deploy' && req.method === 'POST') {
        let body = '';
        req.on('data', (chunk) => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const functionData = JSON.parse(body);
                deployFunction(functionData, res);
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'JSON non valido' }));
            }
        });
        return;
    }
 
    // Nuovo endpoint: Deploy da GitHub
    if (req.url === '/deploy-github' && req.method === 'POST') {
        let body = '';
        req.on('data', (chunk) => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const githubData = JSON.parse(body);
                deployFromGitHub(githubData, res);
            } catch (error) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'JSON non valido' }));
            }
        });
        return;
    }
 
    // Endpoint: Elenco funzioni deployate
    if (req.url === '/functions' && req.method === 'GET') {
        const cmd = `${NUCTL_PATH} get functions -o json --platform local`;

        exec(cmd, { timeout: 10000 }, (error, stdout, stderr) => {
            if (error) {
                console.error(`Errore nel recupero delle funzioni: ${stderr || error.message}`);

                // Se l'output NON è in JSON, gestisci il caso di "nessuna funzione"
                if (stderr.includes('No functions found') || stdout.trim() === '') {
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ functions: [] }));
                    return;
                }

                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    error: 'Errore nel recupero delle funzioni',
                    details: stderr || error.message
                }));
                return;
            }

            try {
                const functions = JSON.parse(stdout);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ functions }));
            } catch (parseError) {
                console.error('Errore parsing JSON:', parseError.message);
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ functions: [] }));
            }
        });
        return;
    }

    // Endpoint non trovato
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint non trovato' }));
});
 
// Deploy da codice inline (originale)
function deployFunction(data, res) {
    const { name, code, runtime = 'golang' } = data;
 
    if (!name || !code) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Nome e codice sono richiesti' }));
        return;
    }
 
    console.log(`Deploy della funzione: ${name}`);
 
    const fileName = `${name}.${runtime === 'golang' ? 'go' : 'py'}`;
    const filePath = `${TEMP_DIR}/${fileName}`;
 
    try {
        fs.writeFileSync(filePath, code);
 
        const cmd = `${NUCTL_PATH} deploy ${name} --path "${filePath}" --runtime ${runtime} --platform local`;
 
        console.log(`Esecuzione: ${cmd}`);
 
        exec(cmd, { timeout: 60000 }, (error, stdout, stderr) => {
            try {
                fs.unlinkSync(filePath);
            } catch (e) {
                console.warn(`Errore rimozione file: ${e.message}`);
            }
 
            if (error) {
                console.error(`Errore deploy: ${error.message}`);
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    error: 'Deploy fallito',
                    details: error.message,
                    stderr: stderr
                }));
                return;
            }
 
            console.log(`Deploy completato: ${name}`);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'success',
                message: `Funzione ${name} deployata con successo`,
                output: stdout
            }));
        });
 
    } catch (fileError) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            error: 'Errore scrittura file',
            details: fileError.message
        }));
    }
}
 
// Nuova funzione: Deploy da GitHub
function deployFromGitHub(data, res) {
    const { name, githubUrl, runtime = 'golang', subPath = '' } = data;
 
    if (!name || !githubUrl) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Nome e URL GitHub sono richiesti' }));
        return;
    }
 
    console.log(`Deploy da GitHub: ${name} - ${githubUrl}`);
 
    // Costruisci il path completo se c'è un subPath
    const fullGithubPath = subPath ? `${githubUrl}/${subPath}` : githubUrl;
 
    // Comando nuctl per deploy da GitHub
    const cmd = `${NUCTL_PATH} deploy ${name} --path "${fullGithubPath}" --runtime ${runtime} --platform local`;
 
    console.log(`Esecuzione: ${cmd}`);
 
    exec(cmd, { timeout: 120000 }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Errore deploy da GitHub: ${error.message}`);
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
            output: stdout
        }));
    });
}
 
// Avvia server
server.listen(PORT, '127.0.0.1', () => {
    console.log(`Server Nuclio in ascolto su porta ${PORT}`);
    console.log(`Directory temporanea: ${TEMP_DIR}`);
    console.log('Endpoints disponibili:');
    console.log('  POST /deploy - Deploy da codice inline');
    console.log('  POST /deploy-github - Deploy da repository GitHub');
    console.log('  GET /health - Health check');
});