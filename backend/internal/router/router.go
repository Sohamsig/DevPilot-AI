package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/chat"
)

func SetupRouter() *gin.Engine {

	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Welcome to DevPilot AI 🚀",
		})
	})

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "DevPilot AI",
			"version": "v0.3.0",
		})
	})

	chat.RegisterRoutes(r)

	return r
}
