package logger

import (
	"log"
	"os"
)

var Log = log.New(
	os.Stdout, "DevPilot AI: ",
	log.Ldate|log.Ltime|log.Lshortfile,
)
