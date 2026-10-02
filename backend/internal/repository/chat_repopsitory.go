package repository

import (
	"context"
	"errors"

	"github.com/sohambabrekar/devpilot-ai/backend/internal/database"
	"github.com/sohambabrekar/devpilot-ai/backend/internal/models"
	"go.mongodb.org/mongo-driver/v2/bson"
)

type ChatRepository struct{}

func NewChatRepository() *ChatRepository {
	return &ChatRepository{}
}

func (r *ChatRepository) Create(chat *models.Chat) error {
	if database.DB == nil {
		return errors.New("database is not initialized")
	}

	_, err := database.DB.
		Collection("chats").
		InsertOne(context.Background(), chat)

	return err
}

func (r *ChatRepository) GetAll() ([]models.Chat, error) {
	if database.DB == nil {
		return nil, errors.New("database is not initialized")
	}

	cursor, err := database.DB.
		Collection("chats").
		Find(context.Background(), bson.D{})

	if err != nil {
		return nil, err
	}
	defer cursor.Close(context.Background())

	var chats []models.Chat

	if err := cursor.All(context.Background(), &chats); err != nil {
		return nil, err
	}

	return chats, nil
}

func (r *ChatRepository) GetByID(id string) (*models.Chat, error) {
	if database.DB == nil {
		return nil, errors.New("database is not initialized")
	}

	objectID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return nil, err
	}

	var chat models.Chat

	err = database.DB.
		Collection("chats").
		FindOne(
			context.Background(),
			bson.M{"_id": objectID},
		).
		Decode(&chat)

	if err != nil {
		return nil, err
	}

	return &chat, nil
}

func (r *ChatRepository) Save(chat models.Chat) error {
	return r.Create(&chat)
}
