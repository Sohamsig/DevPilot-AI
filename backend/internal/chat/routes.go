package chat

import "github.com/gin-gonic/gin"

func RegisterRoutes(r *gin.Engine) {
	r.POST("/chat", ChatHandler)
	r.GET("/chat", GetAllChatsHandler)
	r.GET("/chat/:id", GetChatByIDHandler)
}
