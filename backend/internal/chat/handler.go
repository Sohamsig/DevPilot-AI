package chat

import (
	"net/http"

	"github.com/gin-gonic/gin"
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

	c.JSON(http.StatusOK, ChatResponse{
		Reply: reply,
	})
}
