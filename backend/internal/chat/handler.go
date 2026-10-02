package chat

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/sohambabrekar/devpilot-ai/backend/internal/models"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/repository"
)

// POST /chat
func ChatHandler(c *gin.Context) {

	var req ChatRequest

	// Parse JSON request
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid JSON",
		})
		return
	}

	// Validate request
	if err := ValidateChatRequest(req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	// Generate AI reply
	reply := GenerateReply(req.Message)

	// Create chat document
	chat := &models.Chat{
		Message:   req.Message,
		Reply:     reply,
		CreatedAt: time.Now(),
	}

	// Save to MongoDB
	repo := repository.NewChatRepository()

	if err := repo.Create(chat); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to save chat",
		})
		return
	}

	// Send response
	c.JSON(http.StatusOK, ChatResponse{
		Reply: reply,
	})
}

// GET /chat
func GetAllChatsHandler(c *gin.Context) {

	repo := repository.NewChatRepository()

	chats, err := repo.GetAll()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to fetch chats",
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"count":   len(chats),
		"data":    chats,
	})
}

func GetChatByIDHandler(c *gin.Context) {

	id := c.Param("id")

	repo := repository.NewChatRepository()

	chat, err := repo.GetByID(id)

	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Chat not found",
		})
		return
	}

	c.JSON(http.StatusOK, chat)
}
