package handler

import (
	"context"
	"net/http"
	"strconv"

	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/Tencent/WeKnora/internal/types/interfaces"
	secutils "github.com/Tencent/WeKnora/internal/utils"
	"github.com/gin-gonic/gin"
)

// KnowledgeBaseHandler defines the HTTP handler for knowledge base operations
type KnowledgeBaseHandler struct {
	service          interfaces.KnowledgeBaseService
	knowledgeService interfaces.KnowledgeService
}

// NewKnowledgeBaseHandler creates a new knowledge base handler instance
func NewKnowledgeBaseHandler(
	service interfaces.KnowledgeBaseService,
	knowledgeService interfaces.KnowledgeService,
) *KnowledgeBaseHandler {
	return &KnowledgeBaseHandler{service: service, knowledgeService: knowledgeService}
}

// HybridSearch handles requests to perform hybrid vector and keyword search on a knowledge base
func (h *KnowledgeBaseHandler) HybridSearch(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start hybrid search")

	// Validate knowledge base ID
	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Knowledge base ID is empty")
		c.Error(errors.NewBadRequestError("Knowledge base ID cannot be empty"))
		return
	}

	// Parse request body
	var req types.SearchParams
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError("Invalid request parameters").WithDetails(err.Error()))
		return
	}

	logger.Infof(ctx, "Executing hybrid search, knowledge base ID: %s, query: %s",
		secutils.SanitizeForLog(id), secutils.SanitizeForLog(req.QueryText))

	// Execute hybrid search with default search parameters
	results, err := h.service.HybridSearch(ctx, id, req)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Hybrid search completed, knowledge base ID: %s, result count: %d",
		secutils.SanitizeForLog(id), len(results))
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    results,
	})
}

// CreateKnowledgeBase handles requests to create a new knowledge base
func (h *KnowledgeBaseHandler) CreateKnowledgeBase(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start creating knowledge base")

	// Parse request body
	var req types.KnowledgeBase
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError("Invalid request parameters").WithDetails(err.Error()))
		return
	}
	if err := validateExtractConfig(req.ExtractConfig); err != nil {
		logger.Error(ctx, "Invalid extract configuration", err)
		c.Error(err)
		return
	}

	logger.Infof(ctx, "Creating knowledge base, name: %s", secutils.SanitizeForLog(req.Name))
	// Create knowledge base using the service
	kb, err := h.service.CreateKnowledgeBase(ctx, &req)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Knowledge base created successfully, ID: %s, name: %s",
		secutils.SanitizeForLog(kb.ID), secutils.SanitizeForLog(kb.Name))
	c.JSON(http.StatusCreated, gin.H{
		"success": true,
		"data":    kb,
	})
}

// validateAndGetKnowledgeBase validates request parameters and retrieves the knowledge base
// Returns the knowledge base, knowledge base ID, and any errors encountered
func (h *KnowledgeBaseHandler) validateAndGetKnowledgeBase(c *gin.Context) (*types.KnowledgeBase, string, error) {
	ctx := c.Request.Context()

	// Get tenant ID from context
	tenantID, exists := c.Get(types.TenantIDContextKey.String())
	if !exists {
		logger.Error(ctx, "Failed to get tenant ID")
		return nil, "", errors.NewUnauthorizedError("Unauthorized")
	}

	// Get knowledge base ID from URL parameter
	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Knowledge base ID is empty")
		return nil, "", errors.NewBadRequestError("Knowledge base ID cannot be empty")
	}

	// Verify tenant has permission to access this knowledge base
	kb, err := h.service.GetKnowledgeBaseByID(ctx, id)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		return nil, id, errors.NewInternalServerError(err.Error())
	}

	// Verify tenant ownership
	if kb.TenantID != tenantID.(uint64) {
		logger.Warnf(
			ctx,
			"Tenant has no permission to access this knowledge base, knowledge base ID: %s, "+
				"request tenant ID: %d, knowledge base tenant ID: %d",
			id, tenantID.(uint64), kb.TenantID,
		)
		return nil, id, errors.NewForbiddenError("No permission to operate")
	}

	return kb, id, nil
}

// GetKnowledgeBase handles requests to retrieve a knowledge base by ID
func (h *KnowledgeBaseHandler) GetKnowledgeBase(c *gin.Context) {
	// Validate and get the knowledge base
	kb, _, err := h.validateAndGetKnowledgeBase(c)
	if err != nil {
		c.Error(err)
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    kb,
	})
}

// ListKnowledgeBases handles requests to list all knowledge bases for a tenant
func (h *KnowledgeBaseHandler) ListKnowledgeBases(c *gin.Context) {
	ctx := c.Request.Context()

	// Get all knowledge bases for this tenant
	kbs, err := h.service.ListKnowledgeBases(ctx)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    kbs,
	})
}

// UpdateKnowledgeBaseRequest defines the request body structure for updating a knowledge base
type UpdateKnowledgeBaseRequest struct {
	Name        string                     `json:"name"        binding:"required"`
	Description string                     `json:"description"`
	Config      *types.KnowledgeBaseConfig `json:"config"      binding:"required"`
}

// UpdateKnowledgeBase handles requests to update an existing knowledge base
func (h *KnowledgeBaseHandler) UpdateKnowledgeBase(c *gin.Context) {
	ctx := c.Request.Context()
	logger.Info(ctx, "Start updating knowledge base")

	// Validate and get the knowledge base
	_, id, err := h.validateAndGetKnowledgeBase(c)
	if err != nil {
		c.Error(err)
		return
	}

	// Parse request body
	var req UpdateKnowledgeBaseRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError("Invalid request parameters").WithDetails(err.Error()))
		return
	}

	logger.Infof(ctx, "Updating knowledge base, ID: %s, name: %s",
		secutils.SanitizeForLog(id), secutils.SanitizeForLog(req.Name))

	// Update the knowledge base
	kb, err := h.service.UpdateKnowledgeBase(ctx, id, req.Name, req.Description, req.Config)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Knowledge base updated successfully, ID: %s",
		secutils.SanitizeForLog(id))
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    kb,
	})
}

// DeleteKnowledgeBase handles requests to delete a knowledge base
func (h *KnowledgeBaseHandler) DeleteKnowledgeBase(c *gin.Context) {
	ctx := c.Request.Context()
	logger.Info(ctx, "Start deleting knowledge base")

	// Validate and get the knowledge base
	kb, id, err := h.validateAndGetKnowledgeBase(c)
	if err != nil {
		c.Error(err)
		return
	}

	logger.Infof(ctx, "Deleting knowledge base, ID: %s, name: %s",
		secutils.SanitizeForLog(id), secutils.SanitizeForLog(kb.Name))

	// Delete the knowledge base
	if err := h.service.DeleteKnowledgeBase(ctx, id); err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Knowledge base deleted successfully, ID: %s",
		secutils.SanitizeForLog(id))
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Knowledge base deleted successfully",
	})
}

type CopyKnowledgeBaseRequest struct {
	SourceID string `json:"source_id" binding:"required"`
	TargetID string `json:"target_id"`
}

func (h *KnowledgeBaseHandler) CopyKnowledgeBase(c *gin.Context) {
	ctx := c.Request.Context()
	var req CopyKnowledgeBaseRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError("Invalid request parameters").WithDetails(err.Error()))
		return
	}

	go func(ctx context.Context) {
		err := h.knowledgeService.CloneKnowledgeBase(ctx, req.SourceID, req.TargetID)
		if err != nil {
			logger.Errorf(ctx, "Failed to copy knowledge base, ID: %s to ID: %s",
				secutils.SanitizeForLog(req.SourceID), secutils.SanitizeForLog(req.TargetID))
			return
		}
		logger.Infof(ctx, "Knowledge base copy from ID: %s to ID: %s successfully",
			secutils.SanitizeForLog(req.SourceID), secutils.SanitizeForLog(req.TargetID))
	}(logger.CloneContext(ctx))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Knowledge base copy successfully",
	})
}

// validateExtractConfig validates the graph configuration parameters
func validateExtractConfig(config *types.ExtractConfig) error {
	logger.Errorf(context.Background(), "Validating extract configuration: %+v", config)
	if config == nil {
		return nil
	}
	if !config.Enabled {
		*config = types.ExtractConfig{Enabled: false}
		return nil
	}
	// Validate text field
	if config.Text == "" {
		return errors.NewBadRequestError("text cannot be empty")
	}

	// Validate tags field
	if len(config.Tags) == 0 {
		return errors.NewBadRequestError("tags cannot be empty")
	}
	for i, tag := range config.Tags {
		if tag == "" {
			return errors.NewBadRequestError("tag cannot be empty at index " + strconv.Itoa(i))
		}
	}

	// Validate nodes
	if len(config.Nodes) == 0 {
		return errors.NewBadRequestError("nodes cannot be empty")
	}
	nodeNames := make(map[string]bool)
	for i, node := range config.Nodes {
		if node.Name == "" {
			return errors.NewBadRequestError("node name cannot be empty at index " + strconv.Itoa(i))
		}
		// Check for duplicate node names
		if nodeNames[node.Name] {
			return errors.NewBadRequestError("duplicate node name: " + node.Name)
		}
		nodeNames[node.Name] = true
	}

	if len(config.Relations) == 0 {
		return errors.NewBadRequestError("relations cannot be empty")
	}
	// Validate relations
	for i, relation := range config.Relations {
		if relation.Node1 == "" {
			return errors.NewBadRequestError("relation node1 cannot be empty at index " + strconv.Itoa(i))
		}
		if relation.Node2 == "" {
			return errors.NewBadRequestError("relation node2 cannot be empty at index " + strconv.Itoa(i))
		}
		if relation.Type == "" {
			return errors.NewBadRequestError("relation type cannot be empty at index " + strconv.Itoa(i))
		}
		// Check if referenced nodes exist
		if !nodeNames[relation.Node1] {
			return errors.NewBadRequestError("relation references non-existent node1: " + relation.Node1)
		}
		if !nodeNames[relation.Node2] {
			return errors.NewBadRequestError("relation references non-existent node2: " + relation.Node2)
		}
	}

	return nil
}
