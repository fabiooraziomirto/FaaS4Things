'use strict';
 
const http = require('http');
const { exec } = require('child_process');
 
const PORT = process.env.PORT || 8080;
const HOST = '0.0.0.0';
 
const COMMAND = "./nuctl deploy -p https://raw.githubusercontent.com/nuclio/nuclio/master/hack/examples/golang/helloworld/helloworld.go --registry localhost:5000 helloworld --run-registry localhost:5000 --platform local";
 
const server = http.createServer(function(req, res) {
  const url = req.url;
  const method = req.method;
 
  console.log('[' + new Date().toISOString() + '] ' + method + ' ' + url);
 
  if (method === 'GET' && url === '/fn1') {
    console.log('Richiesta ricevuta su /fn1, esecuzione comando...');
   
 
    exec(COMMAND, function(error, stdout, stderr) {
      console.log('Esecuzione comando completata');
     
      if (error) {
        console.error('Errore durante l\'esecuzione del comando:', error);
        console.error('STDERR:', stderr);
       
 
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'error',
          message: 'Errore durante l\'esecuzione del comando',
          error: error.message,
          stderr: stderr
        }));
        return;
      }
     
      console.log('STDOUT:', stdout);
     
 
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'success',
        message: 'Comando eseguito con successo',
        timestamp: new Date().toISOString(),
        output: stdout
      }));
    });
  } else {
 
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'error',
      message: 'Endpoint non trovato'
    }));
  }
});
 
 
server.listen(PORT, HOST, function() {
  console.log('Server in ascolto su http://' + HOST + ':' + PORT);
  console.log('Pronto a ricevere richieste GET su /fn1');
});
 
 
process.on('SIGTERM', function() {
  console.log('SIGTERM ricevuto, chiusura del server...');
  server.close(function() {
    console.log('Server chiuso');
    process.exit(0);
  });
});