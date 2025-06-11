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

