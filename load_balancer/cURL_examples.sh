curl -X POST http://localhost:5000/deploy-to \
     -H "Content-Type: application/json" \
     -d '{
           "nodeUrl": "http://192.168.1.100:8000",
           "name": "funzione-diretta",
           "code": "def handler(context, event):\n    return \"Hello from specific node!\"",
           "runtime": "python"
         }'

curl -X POST http://localhost:5000/deploy-github-to \
  -H "Content-Type: application/json" \
  -d '{
    "targetNode": "http://192.168.1.101:8000",
    "name": "github-specific",
    "runtime": "golang",
    "githubUrl": "https://github.com/tuo-utente/tuo-repo"
}'

curl -X POST http://localhost:8888/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-inline",
    "runtime": "python",
    "code": "def handler(context, event):\n    return \\"Hello from inline\\""
}'


curl -X POST http://localhost:8888/deploy-github \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-github",
    "runtime": "golang",
    "githubUrl": "https://github.com/tuo-utente/tuo-repo"
}'

###Curl cloverleaf###
curl -X POST http://192.168.1.246:5002/deploy-github   -H "Content-Type: application/json"   -d '{
      "name": "pippo",
      "githubUrl": "https://raw.githubusercontent.com/fabiooraziomirto/FaaS4Things/refs/heads/cloverleaf/handler_python.py",
      "runtime": "python",
      "platform": "local",
      "buildCommand": "pip install requests",
      "handler": "handler_python:handler"
  }'

###CURL CLOVERLEAF NUOVO HANDLER CON ISTRUZIONI
curl -X POST http://192.168.1.246:5002/deploy-github   -H "Content-Type: application/json"   -d '{
    "name": "istruzione1-fn",
    "githubUrl": "https://raw.githubusercontent.com/fabiooraziomirto/FaaS4Things/refs/heads/clover_LB/handler.py",
    "runtime": "python",
    "platform": "local",
    "buildCommand": "pip install requests",
    "handler": "handler:handler",
    "env": [
      {"name": "INSTRUCTION_TYPE", "value": "istruzione1"},
      {"name": "FORWARD_SECRET", "value": "forward_secret_123"},
      {"name": "FORWARD_URL", "value": "http://10.42.1.70:3000/forward"}
    ]
  }'

####curl dentro LR######
curl -X POST http://localhost:32768 \
  -H "Content-Type: application/json" \
  -d '{"variable": "server1", "function": "getData"}'
