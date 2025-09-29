######CURL GENERICA SENZA SEC
curl -X POST http://localhost:3000/forward \
  -H "Content-Type: application/json" \
  -d '{"variable": "server1", "function": "getData"}'

####CON SEC
# 1. Imposta il segreto (deve essere lo stesso usato da serverino & mock)
SECRET="mio_super_segreto_123"

# 2. Prepara il payload
BODY='{"variable":"server1","function":"getData"}'

# 3. Genera timestamp corrente
TS=$(date +%s)

# 4. Calcola la firma HMAC-SHA256
SIG=$(printf "%s:%s" "$BODY" "$TS" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

# 5. Fai la curl con gli header
curl -X POST http://localhost:3000/forward \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIG" \
  -H "X-Signature-Timestamp: $TS" \
  -d "$BODY"

