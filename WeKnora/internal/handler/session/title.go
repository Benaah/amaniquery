package session

import (
	"net/http"

	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/gin-gonic/gin"
)

// GenerateTitle generates a title for a session based on message content
func (h *Handler) GenerateTitle(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start generating session title")

	// Get session ID from URL parameter
	sessionID := c.Param("session_id")
	if sessionID == "" {
		logger.Error(ctx, "Session ID is empty")
		c.Error(errors.NewBadRequestError(errors.ErrInvalidSessionID.Error()))
		return
	}

	// Parse request body
	var request GenerateTitleRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		logger.Error(ctx, "Failed to parse request data", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}

	// Get session from database
	session, err := h.sessionService.GetSession(ctx, sessionID)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Call service to generate title
	logger.Infof(ctx, "Generating session title, session ID: %s, message count: %d", sessionID, len(request.Messages))
	title, err := h.sessionService.GenerateTitle(ctx, session, request.Messages)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return generated title
	logger.Infof(ctx, "Session title generated successfully, session ID: %s, title: %s", sessionID, title)
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    title,
	})
}
