package main

import (
	"io/ioutil"
	"github.com/nuclio/nuclio-sdk-go"
)

// Handler - Complessità O(n³) - Legge il file n² volte
// Dove n è proporzionale alla dimensione del file
func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
	// Prima leggiamo il file per ottenere la sua dimensione - O(n)
	fileContent, err := ioutil.ReadFile("file.txt")
	if err != nil {
		return nuclio.Response{
			StatusCode:  500,
			ContentType: "application/text",
			Body:        []byte("Errore nella lettura del file: " + err.Error()),
		}, err
	}

	// Determiniamo la dimensione del file
	n := len(fileContent)
	
	// Leggiamo il file n² volte - O(n³)
	// Poiché ogni lettura è O(n) e la facciamo n² volte
	lastContent := []byte{}
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			// Leggiamo il file ogni volta - estremamente inefficiente ma dimostra O(n³)
			lastContent, err = ioutil.ReadFile("file.txt")
			if err != nil {
				return nuclio.Response{
					StatusCode:  500,
					ContentType: "application/text",
					Body:        []byte("Errore nella lettura del file: " + err.Error()),
				}, err
			}
		}
	}

	// Restituiamo l'ultimo contenuto letto
	return nuclio.Response{
		StatusCode:  200,
		ContentType: "application/text",
		Body:        lastContent,
	}, nil
}
