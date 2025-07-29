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

func bubbleSort(arr []int) {
	n := len(arr)
	for i := 0; i < n-1; i++ {
		for j := 0; j < n-i-1; j++ {
			if arr[j] > arr[j+1] {
				arr[j], arr[j+1] = arr[j+1], arr[j]
			}
		}
	}
}

func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
	size := 1000
	// Array nel caso peggiore: elementi da size-1 a 0 (decrescente)
	arr := make([]int, size)
	for i := 0; i < size; i++ {
		arr[i] = size - 1 - i
	}

	start := time.Now()
	bubbleSort(arr)
	duration := time.Since(start)

	context.Logger.Info("Bubble sort completed", "duration", duration)

	// Restituisco solo il tempo e una conferma (non tutto l'array per performance)
	body := fmt.Sprintf("Bubble sort of %d elements completed.\nExecution time: %s", size, duration)

	return nuclio.Response{
		StatusCode:  200,
		ContentType: "application/text",
		Body:        []byte(body),
	}, nil
}
