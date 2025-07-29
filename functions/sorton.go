package main
 
import (
	"encoding/json"
	"fmt"
	"time"
 
	"github.com/nuclio/nuclio-sdk-go"
)
 
// ResponseBody rappresenta la struttura della risposta di successo
type ResponseBody struct {
	Array               []int   `json:"array"`
	Sum                 int     `json:"sum"`
	ArraySize          int     `json:"array_size"`
	ExecutionTimeSeconds float64 `json:"execution_time_seconds"`
	Complexity         string  `json:"complexity"`
	Timestamp          float64 `json:"timestamp"`
}
 
// ErrorResponse rappresenta la struttura della risposta di errore
type ErrorResponse struct {
	Error     string  `json:"error"`
	Message   string  `json:"message"`
	Timestamp float64 `json:"timestamp"`
}
 
// Handler è la funzione principale del servizio Nuclio
func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
	context.Logger.Info("Eseguendo operazioni lineari O(n) su array statico di 100 elementi...")
 
	// Array statico di 1000 elementi (da 0 a 999, come nell'originale Python)
	data := make([]int, 1000)
	for i := 0; i < 1000; i++ {
		data[i] = i
	}
	context.Logger.InfoWith("Usando array statico", "size", len(data))
 
	// Misurazione del tempo di esecuzione
	startTime := time.Now()
	result := sumArray(data)
	endTime := time.Now()
	executionTime := endTime.Sub(startTime).Seconds()
 
	context.Logger.InfoWith("Somma calcolata", 
		"result", result, 
		"execution_time", fmt.Sprintf("%.6f secondi", executionTime))
 
	// Creazione della risposta
	responseBody := ResponseBody{
		Array:               data,
		Sum:                 result,
		ArraySize:          len(data),
		ExecutionTimeSeconds: executionTime,
		Complexity:         "O(n)",
		Timestamp:          float64(time.Now().Unix()),
	}
 
	// Serializzazione JSON
	jsonResponse, err := json.MarshalIndent(responseBody, "", "  ")
	if err != nil {
		context.Logger.ErrorWith("Errore durante la serializzazione JSON", "error", err)
		errorResponse := ErrorResponse{
			Error:     err.Error(),
			Message:   "Errore durante la serializzazione",
			Timestamp: float64(time.Now().Unix()),
		}
		return nuclio.Response{
			StatusCode: 500,
			ContentType: "application/json",
			Body:       errorResponse,
		}, nil
	}
 
	// Ritorno della risposta di successo
	return nuclio.Response{
		StatusCode: 200,
		ContentType: "application/json",
		Headers: map[string]interface{}{
			"Content-Type": "application/json",
		},
		Body: string(jsonResponse),
	}, nil
}
 
// sumArray calcola la somma di tutti gli elementi dell'array
func sumArray(arr []int) int {
	total := 0
	for _, val := range arr {
		total += val
	}
	return total
}
