package main

import (
	"io/ioutil"
	"github.com/nuclio/nuclio-sdk-go"
)

// HandlerOn - Complessità O(n) - Legge il file una sola volta
// La complessità è lineare rispetto alla dimensione del file
func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
	// Leggiamo il file una volta - O(n)
	fileContent, err := ioutil.ReadFile("file.txt")
	if err != nil {
		return nuclio.Response{
			StatusCode:  500,
			ContentType: "application/text",
			Body:        []byte("Errore nella lettura del file: " + err.Error()),
		}, err
	}

	// Eseguiamo "cat file.txt" una volta
	return nuclio.Response{
		StatusCode:  200,
		ContentType: "application/text",
		Body:        fileContent,
	}, nil
}
