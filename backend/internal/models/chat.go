package models

import (
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
)

type Chat struct {
	ID        bson.ObjectID `bson:"_id,omitempty" json:"id"`
	Message   string        `bson:"message" json:"message"`
	Reply     string        `bson:"reply" json:"reply"`
	CreatedAt time.Time     `bson:"created_at" json:"created_at"`
}
