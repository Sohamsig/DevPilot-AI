package main

import (
	"fmt"

	"github.com/sohambabrekar/devpilot-ai/backend/internal/config"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/router"
)

func main() {

	cfg := config.LoadConfig()

	r := router.SetupRouter()

	fmt.Println("🚀 DevPilot AI running on port", cfg.Port)

	if err := r.Run(":" + cfg.Port); err != nil {
		panic(err)
	}
}
