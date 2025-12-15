package interfaces

import (
	"context"

	"github.com/hibiken/asynq"
)

// Extracter is a interface for extracting entities
type Extracter interface {
	// Extract extracts entities from a task
	Extract(ctx context.Context, t *asynq.Task) error
}
