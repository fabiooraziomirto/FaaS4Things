package main
 
import (
    "io"
    "net/http"
    "os"
    "github.com/nuclio/nuclio-sdk-go"
)
 
const eventLogFilePath = "/tmp/events.json"
const iotronicServiceURL = "http://10.43.100.186:50061/fn1"
 
func Handler(context *nuclio.Context, event nuclio.Event) (interface{}, error) {
    context.Logger.InfoWith("Received event", "body", string(event.GetBody()))
    // if we got the event from rabbit
    if event.GetTriggerInfo().GetClass() == "async" && event.GetTriggerInfo().GetKind() == "rabbitMq" {
        // Effettua la chiamata HTTP GET al servizio iotronic-wstun
        resp, err := http.Get(iotronicServiceURL)
        if err != nil {
            context.Logger.ErrorWith("Failed to call iotronic-wstun service", "error", err)
            // Continua l'esecuzione anche in caso di errore nella chiamata HTTP
        } else {
            defer resp.Body.Close()
            context.Logger.InfoWith("Successfully called iotronic-wstun service", "statusCode", resp.StatusCode)
        }
 
        eventLogFile, err := os.OpenFile(eventLogFilePath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
        if err != nil {
            return nil, err
        }
        defer eventLogFile.Close()
        // write the body followed by ', '
        for _, dataToWrite := range [][]byte{
            event.GetBody(),
            []byte(", "),
        } {
            // write the thing to write
            if _, err = eventLogFile.Write(dataToWrite); err != nil {
                return nil, err
            }
        }
        // all's well
        return nil, nil
    }
    // open the log for read
    eventLogFile, err := os.OpenFile(eventLogFilePath, os.O_RDONLY, 0600)
    if err != nil {
        return nil, err
    }
    defer eventLogFile.Close()
    // read the entire file
    eventLogFileContents, err := io.ReadAll(eventLogFile)
    if err != nil {
        return nil, err
    }
    // chop off the last 2 chars and enclose in a [ ]
    eventLogFileContentsString := "[" + string(eventLogFileContents[:len(eventLogFileContents)-2]) + "]"
    // return the contents as JSON
    return nuclio.Response{
        StatusCode: http.StatusOK,
        ContentType: "application/json",
        Body: []byte(eventLogFileContentsString),
    }, nil
}