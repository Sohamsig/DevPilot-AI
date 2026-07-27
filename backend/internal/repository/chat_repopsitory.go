package repository

import (
	"context"

	"github.com/sohambabrekar/devpilot-ai/backend/internal/database"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/models"
)

type ChatRepository struct{}

func (r *ChatRepository) Save(chat models.Chat) error {

	_, err := database.DB.
		Collection("chats").
		InsertOne(context.Background(), chat)

	return err
}
