package middleware

import (
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/logger"
)

func LoggerMiddleware() gin.HandlerFunc {

	return func(c *gin.Context) {

		start := time.Now()

		c.Next()

		logger.Log.Printf(
			"%s %s %d %v",
			c.Request.Method,
			c.Request.URL.Path,
			c.Writer.Status(),
			time.Since(start),
		)
	}
}
