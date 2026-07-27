package main

import (
	"fmt"

	"github.com/sohambabrekar/devpilot-ai/backend/internal/config"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/database"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/logger"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/router"
)

func main() {
	logger.Init()

	cfg := config.LoadConfig()

	err := database.Connect(
		cfg.MongoURI,
		cfg.DatabaseName,
	)
	if err != nil {
		panic(err)
	}

	r := router.SetupRouter()

	fmt.Println("====================================")
	fmt.Println(cfg.AppName)
	fmt.Println("Environment :", cfg.AppEnv)
	fmt.Println("Port        :", cfg.Port)
	fmt.Println("Log Level   :", cfg.LogLevel)
	fmt.Println("====================================")

	if err := r.Run(":" + cfg.Port); err != nil {
		panic(err)
	}
}
