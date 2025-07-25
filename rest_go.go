package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"

	"github.com/nuclio/nuclio-sdk-go"
)

// Payload è la struttura dati che verrà inviata al server
type Payload struct {
	Variable string `json:"variable"`
	Function string `json:"function"`
}

func Handler(context nuclio.Context, event nuclio.Event) (interface{}, error) {
	// Esempio di valori statici — puoi recuperarli dinamicamente se vuoi
	variable := "42"
	function := "x^2 + 3"

	// Crea il corpo della richiesta
	payload := Payload{
		Variable: variable,
		Function: function,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal JSON: %v", err)
	}

	// URL del server da contattare
	url := "http://10.42.0.122:3000/forward"

	// Crea la richiesta HTTP
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
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

	// Leggi la risposta
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %v", err)
	}

	// Log della risposta
	context.Logger.InfoWith("Response from server", "body", string(body))

	// Ritorna la risposta come risultato della funzione
	return string(body), nil
}
