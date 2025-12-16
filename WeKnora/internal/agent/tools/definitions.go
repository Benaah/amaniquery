package tools

// AvailableTool defines a simple tool metadata used by settings APIs.
type AvailableTool struct {
	Name        string `json:"name"`
	Label       string `json:"label"`
	Description string `json:"description"`
}

// AvailableToolDefinitions returns the list of tools exposed to the UI.
// Keep this in sync with registered tools in this package.
func AvailableToolDefinitions() []AvailableTool {
	return []AvailableTool{
		{Name: "thinking", Label: "思考", Description: "动态和反思性的问题解决思考工具"},
		{Name: "todo_write", Label: "制定计划", Description: "创建结构化的研究计划"},
		{Name: "grep_chunks", Label: "关键词搜索", Description: "快速定位包含特定关键词的文档和分块"},
		{Name: "knowledge_search", Label: "语义搜索", Description: "理解问题并查找语义相关内容"},
		{Name: "list_knowledge_chunks", Label: "查看文档分块", Description: "获取文档完整分块内容"},
		{Name: "query_knowledge_graph", Label: "查询知识图谱", Description: "从知识图谱中查询关系"},
		{Name: "get_document_info", Label: "获取文档信息", Description: "查看文档元数据"},
		{Name: "database_query", Label: "查询数据库", Description: "查询数据库中的信息"},
	}
}

// DefaultAllowedTools returns the default allowed tools list.
func DefaultAllowedTools() []string {
	return []string{
		"thinking",
		"todo_write",
		"knowledge_search",
		"grep_chunks",
		"list_knowledge_chunks",
		"query_knowledge_graph",
		"get_document_info",
		"database_query",
	}
}
