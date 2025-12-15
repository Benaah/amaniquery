package session

import (
	"context"
	"net/http"

	"github.com/Tencent/WeKnora/internal/config"
	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/Tencent/WeKnora/internal/types/interfaces"
	secutils "github.com/Tencent/WeKnora/internal/utils"
	"github.com/gin-gonic/gin"
)

// Handler handles all HTTP requests related to conversation sessions
type Handler struct {
	messageService       interfaces.MessageService       // Service for managing messages
	sessionService       interfaces.SessionService       // Service for managing sessions
	streamManager        interfaces.StreamManager        // Manager for handling streaming responses
	config               *config.Config                  // Application configuration
	knowledgebaseService interfaces.KnowledgeBaseService // Service for managing knowledge bases
}

// NewHandler creates a new instance of Handler with all necessary dependencies
func NewHandler(
	sessionService interfaces.SessionService,
	messageService interfaces.MessageService,
	streamManager interfaces.StreamManager,
	config *config.Config,
	knowledgebaseService interfaces.KnowledgeBaseService,
) *Handler {
	return &Handler{
		sessionService:       sessionService,
		messageService:       messageService,
		streamManager:        streamManager,
		config:               config,
		knowledgebaseService: knowledgebaseService,
	}
}

// CreateSession handles the creation of a new conversation session
func (h *Handler) CreateSession(c *gin.Context) {
	ctx := c.Request.Context()
	// Parse and validate the request body
	var request CreateSessionRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		logger.Error(ctx, "Failed to validate session creation parameters", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}

	// Get tenant ID from context
	tenantID, exists := c.Get(types.TenantIDContextKey.String())
	if !exists {
		logger.Error(ctx, "Failed to get tenant ID")
		c.Error(errors.NewUnauthorizedError("Unauthorized"))
		return
	}

	// Validate session creation request
	// Sessions are now knowledge-base-independent:
	// - KnowledgeBaseID is optional during session creation
	// - Knowledge base can be specified in each query request (AgentQA/KnowledgeQA)
	// - Agent mode can access multiple knowledge bases via AgentConfig.KnowledgeBases
	// - Knowledge base can be switched during conversation
	isAgentMode := request.AgentConfig != nil && request.AgentConfig.AgentModeEnabled
	hasAgentKnowledgeBases := request.AgentConfig != nil && len(request.AgentConfig.KnowledgeBases) > 0

	logger.Infof(
		ctx,
		"Processing session creation request, tenant ID: %d, knowledge base ID: %s, agent mode: %v, agent KBs: %v",
		tenantID,
		request.KnowledgeBaseID,
		isAgentMode,
		hasAgentKnowledgeBases,
	)

	// Create session object with base properties
	createdSession := &types.Session{
		TenantID:        tenantID.(uint64),
		KnowledgeBaseID: request.KnowledgeBaseID,
		AgentConfig:     request.AgentConfig, // Set agent config if provided
	}

	// If summary model parameters are empty, set defaults
	if request.SessionStrategy != nil {
		createdSession.RerankModelID = request.SessionStrategy.RerankModelID
		createdSession.SummaryModelID = request.SessionStrategy.SummaryModelID
		createdSession.MaxRounds = request.SessionStrategy.MaxRounds
		createdSession.EnableRewrite = request.SessionStrategy.EnableRewrite
		createdSession.FallbackStrategy = request.SessionStrategy.FallbackStrategy
		createdSession.FallbackResponse = request.SessionStrategy.FallbackResponse
		createdSession.EmbeddingTopK = request.SessionStrategy.EmbeddingTopK
		createdSession.KeywordThreshold = request.SessionStrategy.KeywordThreshold
		createdSession.VectorThreshold = request.SessionStrategy.VectorThreshold
		createdSession.RerankTopK = request.SessionStrategy.RerankTopK
		createdSession.RerankThreshold = request.SessionStrategy.RerankThreshold
		if request.SessionStrategy.SummaryParameters != nil {
			createdSession.SummaryParameters = request.SessionStrategy.SummaryParameters
		} else {
			createdSession.SummaryParameters = h.createDefaultSummaryConfig(ctx)
		}
		h.fillSummaryConfigDefaults(ctx, createdSession.SummaryParameters)

		logger.Debug(ctx, "Custom session strategy set")
	} else {
		tenantInfo, _ := ctx.Value(types.TenantInfoContextKey).(*types.Tenant)
		h.applyConversationDefaults(ctx, createdSession, tenantInfo)
		logger.Debug(ctx, "Using default session strategy")
	}

	// Fetch knowledge base if KnowledgeBaseID is provided to inherit its model configurations
	// If no KB is provided, models will be determined at query time or use tenant/system defaults
	if request.KnowledgeBaseID != "" {
		kb, err := h.knowledgebaseService.GetKnowledgeBaseByID(ctx, request.KnowledgeBaseID)
		if err != nil {
			logger.Error(ctx, "Failed to get knowledge base", err)
			c.Error(errors.NewInternalServerError(err.Error()))
			return
		}

		// Use knowledge base's summary model if session doesn't specify it
		if createdSession.SummaryModelID == "" {
			createdSession.SummaryModelID = kb.SummaryModelID
		}

		logger.Debugf(ctx, "Knowledge base fetched: %s, summary model: %s",
			kb.ID, kb.SummaryModelID)
	} else {
		logger.Debug(ctx, "No knowledge base ID provided, models will use session strategy or be determined at query time")
	}

	// Call service to create session
	logger.Infof(ctx, "Calling session service to create session")
	createdSession, err := h.sessionService.CreateSession(ctx, createdSession)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return created session
	logger.Infof(ctx, "Session created successfully, ID: %s", createdSession.ID)
	c.JSON(http.StatusCreated, gin.H{
		"success": true,
		"data":    createdSession,
	})
}

func (h *Handler) applyConversationDefaults(ctx context.Context, session *types.Session, tenant *types.Tenant) {
	session.MaxRounds = h.config.Conversation.MaxRounds
	session.EnableRewrite = h.config.Conversation.EnableRewrite
	session.FallbackStrategy = types.FallbackStrategy(h.config.Conversation.FallbackStrategy)
	session.FallbackResponse = h.config.Conversation.FallbackResponse
	session.EmbeddingTopK = h.config.Conversation.EmbeddingTopK
	session.KeywordThreshold = h.config.Conversation.KeywordThreshold
	session.VectorThreshold = h.config.Conversation.VectorThreshold
	session.RerankThreshold = h.config.Conversation.RerankThreshold
	session.RerankTopK = h.config.Conversation.RerankTopK
	session.RerankModelID = ""
	session.SummaryModelID = ""

	if tenant != nil && tenant.ConversationConfig != nil {
		tc := tenant.ConversationConfig
		session.MaxRounds = tc.MaxRounds
		session.EnableRewrite = tc.EnableRewrite
		if tc.FallbackStrategy != "" {
			session.FallbackStrategy = types.FallbackStrategy(tc.FallbackStrategy)
		}
		if tc.FallbackResponse != "" {
			session.FallbackResponse = tc.FallbackResponse
		}
		session.EmbeddingTopK = tc.EmbeddingTopK
		session.KeywordThreshold = tc.KeywordThreshold
		session.VectorThreshold = tc.VectorThreshold
		session.RerankThreshold = tc.RerankThreshold
		session.RerankTopK = tc.RerankTopK
		if tc.RerankModelID != "" {
			session.RerankModelID = tc.RerankModelID
		}
		if tc.SummaryModelID != "" {
			session.SummaryModelID = tc.SummaryModelID
		}
	}

	session.SummaryParameters = h.createDefaultSummaryConfig(ctx)
}

// GetSession retrieves a session by its ID
func (h *Handler) GetSession(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start retrieving session")

	// Get session ID from URL parameter
	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Session ID is empty")
		c.Error(errors.NewBadRequestError(errors.ErrInvalidSessionID.Error()))
		return
	}

	// Call service to get session details
	logger.Infof(ctx, "Retrieving session, ID: %s", id)
	session, err := h.sessionService.GetSession(ctx, id)
	if err != nil {
		if err == errors.ErrSessionNotFound {
			logger.Warnf(ctx, "Session not found, ID: %s", id)
			c.Error(errors.NewNotFoundError(err.Error()))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return session data
	logger.Infof(ctx, "Session retrieved successfully, ID: %s", id)
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    session,
	})
}

// GetSessionsByTenant retrieves all sessions for the current tenant with pagination
func (h *Handler) GetSessionsByTenant(c *gin.Context) {
	ctx := c.Request.Context()

	// Parse pagination parameters from query
	var pagination types.Pagination
	if err := c.ShouldBindQuery(&pagination); err != nil {
		logger.Error(ctx, "Failed to parse pagination parameters", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}

	// Use paginated query to get sessions
	result, err := h.sessionService.GetPagedSessionsByTenant(ctx, &pagination)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return sessions with pagination data
	c.JSON(http.StatusOK, gin.H{
		"success":   true,
		"data":      result.Data,
		"total":     result.Total,
		"page":      result.Page,
		"page_size": result.PageSize,
	})
}

// UpdateSession updates an existing session's properties
func (h *Handler) UpdateSession(c *gin.Context) {
	ctx := c.Request.Context()

	// Get session ID from URL parameter
	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Session ID is empty")
		c.Error(errors.NewBadRequestError(errors.ErrInvalidSessionID.Error()))
		return
	}

	// Verify tenant ID from context for authorization
	tenantID, exists := c.Get(types.TenantIDContextKey.String())
	if !exists {
		logger.Error(ctx, "Failed to get tenant ID")
		c.Error(errors.NewUnauthorizedError("Unauthorized"))
		return
	}

	// Parse request body to session object
	var session types.Session
	if err := c.ShouldBindJSON(&session); err != nil {
		logger.Error(ctx, "Failed to parse session data", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}

	session.ID = id
	session.TenantID = tenantID.(uint64)

	// Call service to update session
	if err := h.sessionService.UpdateSession(ctx, &session); err != nil {
		if err == errors.ErrSessionNotFound {
			logger.Warnf(ctx, "Session not found, ID: %s", id)
			c.Error(errors.NewNotFoundError(err.Error()))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return updated session
	logger.Infof(ctx, "Session updated successfully, ID: %s", id)
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    session,
	})
}

// DeleteSession deletes a session by its ID
func (h *Handler) DeleteSession(c *gin.Context) {
	ctx := c.Request.Context()

	// Get session ID from URL parameter
	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Session ID is empty")
		c.Error(errors.NewBadRequestError(errors.ErrInvalidSessionID.Error()))
		return
	}

	// Call service to delete session
	if err := h.sessionService.DeleteSession(ctx, id); err != nil {
		if err == errors.ErrSessionNotFound {
			logger.Warnf(ctx, "Session not found, ID: %s", id)
			c.Error(errors.NewNotFoundError(err.Error()))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Return success message
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Session deleted successfully",
	})
}
