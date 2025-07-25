package main
 
import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
 
	"github.com/nuclio/nuclio-sdk-go"
)
 
type Payload struct {
	Variable string `json:"variable"`
	Function string `json:"function"`
}
 
func Handler(ctx nuclio.Context, event nuclio.Event) (interface{}, error) {
	payload := Payload{
		Variable: "42",
		Function: "x^2 + 3",
	}
 
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("json error: %v", err)
	}
 
	req, err := http.NewRequest("POST", "http://10.42.0.182:3000/forward", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("request error: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
 
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP error: %v", err)
	}
	defer resp.Body.Close()
 
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read error: %v", err)
	}
 
	ctx.Logger.InfoWith("Server response", "body", string(body))
	return string(body), nil
}
