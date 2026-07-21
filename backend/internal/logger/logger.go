package logger

import (
	"log"
	"os"
)

var Info *log.Logger
var Error *log.Logger

func Init() {
	Info = log.New(os.Stdout, "[INFO] ", log.Ldate|log.Ltime)
	Error = log.New(os.Stderr, "[ERROR] ", log.Ldate|log.Ltime)
}
