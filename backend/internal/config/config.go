package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	Port     string
	AppName  string
	AppEnv   string
	LogLevel string
}

func LoadConfig() *Config {

	err := godotenv.Load()

	if err != nil {
		log.Println(".env file not found, using system environment variables")
	}

	return &Config{
		Port:     getEnv("PORT", "8080"),
		AppName:  getEnv("APP_NAME", "DevPilot AI"),
		AppEnv:   getEnv("APP_ENV", "development"),
		LogLevel: getEnv("LOG_LEVEL", "debug"),
	}
}

func getEnv(key string, defaultValue string) string {

	value := os.Getenv(key)

	if value == "" {
		return defaultValue
	}

	return value
}
