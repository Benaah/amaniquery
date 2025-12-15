package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/Tencent/WeKnora/internal/errors"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/Tencent/WeKnora/internal/types/interfaces"
	secutils "github.com/Tencent/WeKnora/internal/utils"
)

// TagHandler handles knowledge base tag operations.
type TagHandler struct {
	tagService interfaces.KnowledgeTagService
}

// NewTagHandler creates a new TagHandler.
func NewTagHandler(tagService interfaces.KnowledgeTagService) *TagHandler {
	return &TagHandler{tagService: tagService}
}

// ListTags returns all tags under a knowledge base with statistics.
func (h *TagHandler) ListTags(c *gin.Context) {
	ctx := c.Request.Context()
	kbID := secutils.SanitizeForLog(c.Param("id"))

	var page types.Pagination
	if err := c.ShouldBindQuery(&page); err != nil {
		logger.Error(ctx, "Failed to bind pagination query", err)
		c.Error(errors.NewBadRequestError("分页参数不合法").WithDetails(err.Error()))
		return
	}

	keyword := secutils.SanitizeForLog(c.Query("keyword"))

	tags, err := h.tagService.ListTags(ctx, kbID, &page, keyword)
	if err != nil {
		logger.ErrorWithFields(ctx, err, nil)
		c.Error(err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tags,
	})
}

type createTagRequest struct {
	Name      string `json:"name"       binding:"required"`
	Color     string `json:"color"`
	SortOrder int    `json:"sort_order"`
}

// CreateTag creates a new tag.
func (h *TagHandler) CreateTag(c *gin.Context) {
	ctx := c.Request.Context()
	kbID := secutils.SanitizeForLog(c.Param("id"))

	var req createTagRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to bind create tag payload", err)
		c.Error(errors.NewBadRequestError("请求参数不合法").WithDetails(err.Error()))
		return
	}

	tag, err := h.tagService.CreateTag(ctx, kbID,
		secutils.SanitizeForLog(req.Name), secutils.SanitizeForLog(req.Color), req.SortOrder)
	if err != nil {
		logger.ErrorWithFields(ctx, err, map[string]interface{}{
			"kb_id": kbID,
		})
		c.Error(err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tag,
	})
}

type updateTagRequest struct {
	Name      *string `json:"name"`
	Color     *string `json:"color"`
	SortOrder *int    `json:"sort_order"`
}

// UpdateTag updates an existing tag.
func (h *TagHandler) UpdateTag(c *gin.Context) {
	ctx := c.Request.Context()

	tagID := secutils.SanitizeForLog(c.Param("tag_id"))
	var req updateTagRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Error(ctx, "Failed to bind update tag payload", err)
		c.Error(errors.NewBadRequestError("请求参数不合法").WithDetails(err.Error()))
		return
	}

	tag, err := h.tagService.UpdateTag(ctx, tagID, req.Name, req.Color, req.SortOrder)
	if err != nil {
		logger.ErrorWithFields(ctx, err, map[string]interface{}{
			"tag_id": tagID,
		})
		c.Error(err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tag,
	})
}

// DeleteTag deletes a tag. Use query param force=true to force delete even if referenced.
func (h *TagHandler) DeleteTag(c *gin.Context) {
	ctx := c.Request.Context()
	tagID := secutils.SanitizeForLog(c.Param("tag_id"))

	force := c.Query("force") == "true"

	if err := h.tagService.DeleteTag(ctx, tagID, force); err != nil {
		logger.ErrorWithFields(ctx, err, map[string]interface{}{
			"tag_id": tagID,
		})
		c.Error(err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
	})
}

// NOTE: TagHandler currently exposes CRUD for tags and statistics.
// Knowledge / Chunk tagging is handled via dedicated knowledge and FAQ APIs.
