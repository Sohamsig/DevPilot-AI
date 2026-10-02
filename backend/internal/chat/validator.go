package chat

import (
	"errors"
	"strings"
)

func ValidateChatRequest(req ChatRequest) error {

	if strings.TrimSpace(req.Message) == "" {
		return errors.New("message cannot be empty")
	}
	return nil
}
