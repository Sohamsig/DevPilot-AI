package chat

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/models"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/repository"
)

func ChatHandler(c *gin.Context) {

	var req ChatRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid JSON",
		})
		return
	}

	if err := ValidateChatRequest(req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	reply := GenerateReply(req.Message)
	repo := repository.ChatRepository{}

	repo.Save(models.Chat{
		Message:   req.Message,
		Response:  reply,
		CreatedAt: time.Now(),
	})

	c.JSON(http.StatusOK, ChatResponse{
		Reply: reply,
	})
}
