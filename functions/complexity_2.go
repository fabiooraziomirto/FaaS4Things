package main

import (
	"io/ioutil"
	"github.com/nuclio/nuclio-sdk-go"
)

// Handler - Complessità O(n²) - Legge il file n volte
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
	
	// Leggiamo il file n volte, dove n è proporzionale alla dimensione del file - O(n²)
	// Poiché ogni lettura è O(n) e la facciamo n volte
	lastContent := []byte{}
	for i := 0; i < n; i++ {
		// Leggiamo il file ogni volta - questo è inefficiente ma dimostra O(n²)
		lastContent, err = ioutil.ReadFile("file.txt")
		if err != nil {
			return nuclio.Response{
				StatusCode:  500,
				ContentType: "application/text",
				Body:        []byte("Errore nella lettura del file: " + err.Error()),
			}, err
		}
	}

	// Restituiamo l'ultimo contenuto letto
	return nuclio.Response{
		StatusCode:  200,
		ContentType: "application/text",
		Body:        lastContent,
	}, nil
}
