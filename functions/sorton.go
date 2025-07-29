package main

import (
    "encoding/json"
    "fmt"
    "github.com/nuclio/nuclio-sdk-go"
    "time"
)

func Handler(context nuclio.Context, event nuclio.Event) error {
    context.Logger.Info("Eseguendo operazioni lineari O(n) su array statico di 1000 elementi...")

    data := make([]int, 1000)
    for i := 0; i < 1000; i++ {
        data[i] = i
    }
    context.Logger.InfoWith("Usando array statico", "length", len(data))

    start := time.Now()
    sum := sumArray(data)
    duration := time.Since(start).Seconds()

    context.Logger.InfoWith("Somma calcolata", "sum", sum, "execution_time", duration)

    response := map[string]interface{}{
        "array":                 data,
        "sum":                   sum,
        "array_size":            len(data),
        "execution_time_seconds": duration,
        "complexity":            "O(n)",
        "timestamp":             time.Now().Unix(),
    }

    responseJSON, err := json.MarshalIndent(response, "", "  ")
    if err != nil {
        errMsg := fmt.Sprintf("Errore durante la serializzazione JSON: %s", err.Error())
        context.Logger.Error(errMsg)
        return err
    }

    return context.Response().
        SetStatusCode(200).
        SetHeader("Content-Type", "application/json").
        SetBody(responseJSON).
        Send()
}


func sumArray(arr []int) int {
    total := 0
    for _, val := range arr {
        total += val
    }
    return total
}
