package models

import (
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
)

type Chat struct {
	ID        bson.ObjectID `bson:"_id,omitempty"`
	Message   string        `bson:"message"`
	Response  string        `bson:"response"`
	CreatedAt time.Time     `bson:"created_at"`
}
