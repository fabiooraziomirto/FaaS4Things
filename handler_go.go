package main
 
import (
	"bytes"
	"fmt"
	"io/ioutil"
	"net/http"
 
	"github.com/nuclio/nuclio-sdk-go"
)
 
func Handler(context nuclio.Context, event nuclio.Event) (interface{}, error) {
	// Definisci l’URL del server Node.js
	url := "http://nodejs-pod.rest.svc.cluster.local:3000/endpoint"
 
	// Corpo della richiesta (puoi adattarlo al tuo backend)
	jsonBody := []byte(`{"message": "Function triggered!"}`)
 
	// Crea la richiesta HTTP
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}
 
	req.Header.Set("Content-Type", "application/json")
 
	// Invia la richiesta
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %v", err)
	}
	defer resp.Body.Close()
 
	// Legge la risposta
	body, _ := ioutil.ReadAll(resp.Body)
	context.Logger.InfoWith("Forwarded to Node.js", "response", string(body))
 
	return string(b
