package handler

import (
	"net/http"

	"github.com/Tencent/WeKnora/internal/application/service"
	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/Tencent/WeKnora/internal/types/interfaces"
	secutils "github.com/Tencent/WeKnora/internal/utils"
	"github.com/gin-gonic/gin"
)

// ModelHandler handles HTTP requests for model-related operations
// It implements the necessary methods to create, retrieve, update, and delete models
type ModelHandler struct {
	service interfaces.ModelService
}

// NewModelHandler creates a new instance of ModelHandler
// It requires a model service implementation that handles business logic
// Parameters:
//   - service: An implementation of the ModelService interface
//
// Returns a pointer to the newly created ModelHandler
func NewModelHandler(service interfaces.ModelService) *ModelHandler {
	return &ModelHandler{service: service}
}

// hideSensitiveInfo hides sensitive information (APIKey, BaseURL) for builtin models
// Returns a copy of the model with sensitive fields cleared if it's a builtin model
func hideSensitiveInfo(model *types.Model) *types.Model {
	if !model.IsBuiltin {
		return model
	}

	// Create a copy with sensitive information hidden
	return &types.Model{
		ID:          model.ID,
		TenantID:    model.TenantID,
		Name:        model.Name,
		Type:        model.Type,
		Source:      model.Source,
		Description: model.Description,
		Parameters: types.ModelParameters{
			// Hide APIKey and BaseURL for builtin models
			BaseURL: "",
			APIKey:  "",
			// Keep other parameters like embedding dimensions
			EmbeddingParameters: model.Parameters.EmbeddingParameters,
			ParameterSize:       model.Parameters.ParameterSize,
		},
		IsBuiltin: model.IsBuiltin,
		Status:    model.Status,
		CreatedAt: model.CreatedAt,
		UpdatedAt: model.UpdatedAt,
	}
}

// CreateModelRequest defines the structure for model creation requests
// Contains all fields required to create a new model in the system
type CreateModelRequest struct {
	Name        string                `json:"name"        binding:"required"`
	Type        types.ModelType       `json:"type"        binding:"required"`
	Source      types.ModelSource     `json:"source"      binding:"required"`
	Description string                `json:"description"`
	Parameters  types.ModelParameters `json:"parameters"  binding:"required"`
}

// CreateModel handles the HTTP request to create a new model
// It validates the request, processes it using the model service,
// and returns the created model to the client
// Parameters:
//   - c: Gin context for the HTTP request
func (h *ModelHandler) CreateModel(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start creating model")

	var req CreateModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}
	tenantID := c.GetUint64(types.TenantIDContextKey.String())
	if tenantID == 0 {
		logger.Error(ctx, "Tenant ID is empty")
		c.Error(errors.NewBadRequestError("Tenant ID cannot be empty"))
		return
	}

	logger.Infof(ctx, "Creating model, Tenant ID: %d, Model name: %s, Model type: %s",
		tenantID, secutils.SanitizeForLog(req.Name), secutils.SanitizeForLog(string(req.Type)))

	model := &types.Model{
		TenantID:    tenantID,
		Name:        secutils.SanitizeForLog(req.Name),
		Type:        types.ModelType(secutils.SanitizeForLog(string(req.Type))),
		Source:      req.Source,
		Description: secutils.SanitizeForLog(req.Description),
		Parameters:  req.Parameters,
	}

	if err := h.service.CreateModel(ctx, model); err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(
		ctx,
		"Model created successfully, ID: %s, Name: %s",
		secutils.SanitizeForLog(model.ID),
		secutils.SanitizeForLog(model.Name),
	)

	// Hide sensitive information for builtin models (though newly created models are unlikely to be builtin)
	responseModel := hideSensitiveInfo(model)

	c.JSON(http.StatusCreated, gin.H{
		"success": true,
		"data":    responseModel,
	})
}

// GetModel handles the HTTP request to retrieve a model by its ID
// It fetches the model from the service and returns it to the client,
// or returns appropriate error messages if the model cannot be found
// Parameters:
//   - c: Gin context for the HTTP request
func (h *ModelHandler) GetModel(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start retrieving model")

	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Model ID is empty")
		c.Error(errors.NewBadRequestError("Model ID cannot be empty"))
		return
	}

	logger.Infof(ctx, "Retrieving model, ID: %s", id)
	model, err := h.service.GetModelByID(ctx, id)
	if err != nil {
		if err == service.ErrModelNotFound {
			logger.Warnf(ctx, "Model not found, ID: %s", id)
			c.Error(errors.NewNotFoundError("Model not found"))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Retrieved model successfully, ID: %s, Name: %s", model.ID, model.Name)

	// Hide sensitive information for builtin models
	responseModel := hideSensitiveInfo(model)
	if model.IsBuiltin {
		logger.Infof(ctx, "Builtin model detected, hiding sensitive information for model: %s", model.ID)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    responseModel,
	})
}

// ListModels handles the HTTP request to retrieve all models for a tenant
// It validates the tenant ID, fetches models from the service, and returns them to the client
// Parameters:
//   - c: Gin context for the HTTP request
func (h *ModelHandler) ListModels(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start retrieving model list")

	tenantID := c.GetUint64(types.TenantIDContextKey.String())
	if tenantID == 0 {
		logger.Error(ctx, "Tenant ID is empty")
		c.Error(errors.NewBadRequestError("Tenant ID cannot be empty"))
		return
	}

	models, err := h.service.ListModels(ctx)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Retrieved model list successfully, Tenant ID: %d, Total: %d models", tenantID, len(models))

	// Hide sensitive information for builtin models in the list
	responseModels := make([]*types.Model, len(models))
	for i, model := range models {
		responseModels[i] = hideSensitiveInfo(model)
		if model.IsBuiltin {
			logger.Infof(ctx, "Builtin model detected in list, hiding sensitive information for model: %s", model.ID)
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    responseModels,
	})
}

// UpdateModelRequest defines the structure for model update requests
// Contains fields that can be updated for an existing model
type UpdateModelRequest struct {
	Name        string                `json:"name"`
	Description string                `json:"description"`
	Parameters  types.ModelParameters `json:"parameters"`
	Source      types.ModelSource     `json:"source"`
	Type        types.ModelType       `json:"type"`
}

// UpdateModel handles the HTTP request to update an existing model
// It validates the request, retrieves the current model, applies changes,
// and updates the model in the service
// Parameters:
//   - c: Gin context for the HTTP request
func (h *ModelHandler) UpdateModel(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start updating model")

	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Model ID is empty")
		c.Error(errors.NewBadRequestError("Model ID cannot be empty"))
		return
	}

	var req UpdateModelRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to parse request parameters", err)
		c.Error(errors.NewBadRequestError(err.Error()))
		return
	}

	logger.Infof(ctx, "Retrieving model information, ID: %s", id)
	model, err := h.service.GetModelByID(ctx, id)
	if err != nil {
		if err == service.ErrModelNotFound {
			logger.Warnf(ctx, "Model not found, ID: %s", id)
			c.Error(errors.NewNotFoundError("Model not found"))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	// Update model fields if they are provided in the request
	if req.Name != "" {
		model.Name = req.Name
	}
	model.Description = req.Description
	if req.Parameters != (types.ModelParameters{}) {
		model.Parameters = req.Parameters
	}
	model.Source = req.Source
	model.Type = req.Type

	logger.Infof(ctx, "Updating model, ID: %s, Name: %s", id, model.Name)
	if err := h.service.UpdateModel(ctx, model); err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Model updated successfully, ID: %s", id)

	// Hide sensitive information for builtin models (though builtin models cannot be updated)
	responseModel := hideSensitiveInfo(model)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    responseModel,
	})
}

// DeleteModel handles the HTTP request to delete a model by its ID
// It validates the model ID, attempts to delete the model through the service,
// and returns appropriate status and messages
// Parameters:
//   - c: Gin context for the HTTP request
func (h *ModelHandler) DeleteModel(c *gin.Context) {
	ctx := c.Request.Context()

	logger.Info(ctx, "Start deleting model")

	id := secutils.SanitizeForLog(c.Param("id"))
	if id == "" {
		logger.Error(ctx, "Model ID is empty")
		c.Error(errors.NewBadRequestError("Model ID cannot be empty"))
		return
	}

	logger.Infof(ctx, "Deleting model, ID: %s", id)
	if err := h.service.DeleteModel(ctx, id); err != nil {
		if err == service.ErrModelNotFound {
			logger.Warnf(ctx, "Model not found, ID: %s", id)
			c.Error(errors.NewNotFoundError("Model not found"))
			return
		}
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(errors.NewInternalServerError(err.Error()))
		return
	}

	logger.Infof(ctx, "Model deleted successfully, ID: %s", id)
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Model deleted",
	})
}
