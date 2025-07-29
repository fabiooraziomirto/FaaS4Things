/*
Copyright 2023 The Nuclio Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package main

import (
	"fmt"
    "time"
	"github.com/nuclio/nuclio-sdk-go"
)

func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
    start := time.Now()
	context.Logger.Info("Starting sum calculation")

	var numbers [1000]int
	for i := 0; i < 1000; i++ {
		numbers[i] = 999 - i
	}

	// Calcola la somma
	sum := 0
	for _, num := range numbers {
		sum += num
	}
	duration := time.Since(start)
	context.Logger.Info("Sum: %d, Duration: %s", sum, duration)
    body := fmt.Sprintf("Sum of numbers from 999 to 0 is: %d\nExecution time: %s", sum, duration)

	// Ritorna la somma come stringa nel corpo della risposta
	return nuclio.Response{
		StatusCode:  200,
		ContentType: "application/text",
		Body:        []byte(body),
	}, nil
}
