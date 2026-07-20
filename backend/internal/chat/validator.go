package chat

import "errors"

func ValidateChatRequest(req ChatRequest) error {

	if req.Message == "" {
		return errors.New("message cannot be empty")
	}
	return nil
}
