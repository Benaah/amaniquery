package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"

	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/types"
	"gorm.io/gorm"
)

// DatabaseQueryTool allows AI to query the database with auto-injected tenant_id for security
type DatabaseQueryTool struct {
	BaseTool
	db       *gorm.DB
	tenantID uint64
}

// NewDatabaseQueryTool creates a new database query tool
func NewDatabaseQueryTool(db *gorm.DB, tenantID uint64) *DatabaseQueryTool {
	description := `Execute SQL queries to retrieve information from the database.

## Security Features
- Automatic tenant_id injection: All queries are automatically filtered by the logged-in user's tenant_id
- Read-only queries: Only SELECT statements are allowed
- Safe tables: Only allow queries on authorized tables

## Available Tables and Columns

### knowledge_bases
- id (VARCHAR): Knowledge base ID
- name (VARCHAR): Knowledge base name
- description (TEXT): Description
- tenant_id (INTEGER): Owner tenant ID
- embedding_model_id, summary_model_id, rerank_model_id (VARCHAR): Model IDs
- vlm_config (JSON): Includes VLM settings such as enabled flag and model_id
- created_at, updated_at (TIMESTAMP)

### knowledges (documents)
- id (VARCHAR): Document ID
- tenant_id (INTEGER): Owner tenant ID
- knowledge_base_id (VARCHAR): Parent knowledge base ID
- type (VARCHAR): Document type
- title (VARCHAR): Document title
- description (TEXT): Description
- source (VARCHAR): Source location
- parse_status (VARCHAR): Processing status (unprocessed/processing/completed/failed)
- enable_status (VARCHAR): Enable status (enabled/disabled)
- file_name, file_type (VARCHAR): File information
- file_size, storage_size (BIGINT): Size in bytes
- created_at, updated_at, processed_at (TIMESTAMP)



### chunks
- id (VARCHAR): Chunk ID
- tenant_id (INTEGER): Owner tenant ID
- knowledge_base_id (VARCHAR): Parent knowledge base ID
- knowledge_id (VARCHAR): Parent document ID
- content (TEXT): Chunk content
- chunk_index (INTEGER): Index in document
- is_enabled (BOOLEAN): Enable status
- chunk_type (VARCHAR): Type (text/image/table)
- created_at, updated_at (TIMESTAMP)

## Usage Examples

Query knowledge base information:
{
  "sql": "SELECT id, name, description FROM knowledge_bases ORDER BY created_at DESC LIMIT 10"
}

Count documents by status:
{
  "sql": "SELECT parse_status, COUNT(*) as count FROM knowledges GROUP BY parse_status"
}

Find recent sessions:
{
  "sql": "SELECT id, title, created_at FROM sessions ORDER BY created_at DESC LIMIT 5"
}

Get storage usage:
{
  "sql": "SELECT SUM(storage_size) as total_storage FROM knowledges"
}

Join knowledge bases and documents:
{
  "sql": "SELECT kb.name as kb_name, COUNT(k.id) as doc_count FROM knowledge_bases kb LEFT JOIN knowledges k ON kb.id = k.knowledge_base_id GROUP BY kb.id, kb.name"
}

## Important Notes
- DO NOT include tenant_id in WHERE clause - it's automatically added
- Only SELECT queries are allowed
- Limit results with LIMIT clause for better performance
- Use appropriate JOINs when querying across tables
- All timestamps are in UTC with time zone`

	return &DatabaseQueryTool{
		BaseTool: NewBaseTool("database_query", description),
		db:       db,
		tenantID: tenantID,
	}
}

// Parameters returns the JSON schema for the tool's parameters
func (t *DatabaseQueryTool) Parameters() map[string]interface{} {
	return map[string]interface{}{
		"type": "object",
		"properties": map[string]interface{}{
			"sql": map[string]interface{}{
				"type":        "string",
				"description": "The SELECT SQL query to execute. DO NOT include tenant_id condition - it will be automatically added for security.",
			},
		},
		"required": []string{"sql"},
	}
}

// Execute executes the database query tool
func (t *DatabaseQueryTool) Execute(ctx context.Context, args map[string]interface{}) (*types.ToolResult, error) {
	logger.Infof(ctx, "[Tool][DatabaseQuery] Execute started")

	// Extract SQL from args
	sqlQuery, ok := args["sql"].(string)
	if !ok || sqlQuery == "" {
		logger.Errorf(ctx, "[Tool][DatabaseQuery] Missing or invalid SQL parameter")
		return &types.ToolResult{
			Success: false,
			Error:   "Missing or invalid 'sql' parameter",
		}, fmt.Errorf("missing sql parameter")
	}

	logger.Infof(ctx, "[Tool][DatabaseQuery] Original SQL query:\n%s", sqlQuery)
	logger.Infof(ctx, "[Tool][DatabaseQuery] Tenant ID: %d", t.tenantID)

	// Validate and secure the SQL query
	logger.Debugf(ctx, "[Tool][DatabaseQuery] Validating and securing SQL...")
	securedSQL, err := t.validateAndSecureSQL(sqlQuery)
	if err != nil {
		logger.Errorf(ctx, "[Tool][DatabaseQuery] SQL validation failed: %v", err)
		return &types.ToolResult{
			Success: false,
			Error:   fmt.Sprintf("SQL validation failed: %v", err),
		}, err
	}

	logger.Infof(ctx, "[Tool][DatabaseQuery] Secured SQL query:\n%s", securedSQL)
	logger.Infof(ctx, "Executing secured SQL query - original: %s, secured: %s, tenant_id: %d",
		sqlQuery, securedSQL, t.tenantID)

	// Execute the query
	logger.Infof(ctx, "[Tool][DatabaseQuery] Executing query against database...")
	rows, err := t.db.WithContext(ctx).Raw(securedSQL).Rows()
	if err != nil {
		logger.Errorf(ctx, "[Tool][DatabaseQuery] Query execution failed: %v", err)
		return &types.ToolResult{
			Success: false,
			Error:   fmt.Sprintf("Query execution failed: %v", err),
		}, err
	}
	defer rows.Close()

	logger.Debugf(ctx, "[Tool][DatabaseQuery] Query executed successfully, processing rows...")

	// Get column names
	columns, err := rows.Columns()
	if err != nil {
		return &types.ToolResult{
			Success: false,
			Error:   fmt.Sprintf("Failed to get columns: %v", err),
		}, err
	}

	// Process results
	results := make([]map[string]interface{}, 0)
	for rows.Next() {
		// Create a slice of interface{} to hold each column value
		columnValues := make([]interface{}, len(columns))
		columnPointers := make([]interface{}, len(columns))
		for i := range columnValues {
			columnPointers[i] = &columnValues[i]
		}

		// Scan the row
		if err := rows.Scan(columnPointers...); err != nil {
			return &types.ToolResult{
				Success: false,
				Error:   fmt.Sprintf("Failed to scan row: %v", err),
			}, err
		}

		// Create a map for this row
		rowMap := make(map[string]interface{})
		for i, colName := range columns {
			val := columnValues[i]
			// Convert []byte to string for better readability
			if b, ok := val.([]byte); ok {
				rowMap[colName] = string(b)
			} else {
				rowMap[colName] = val
			}
		}
		results = append(results, rowMap)
	}

	if err := rows.Err(); err != nil {
		return &types.ToolResult{
			Success: false,
			Error:   fmt.Sprintf("Error iterating rows: %v", err),
		}, err
	}

	logger.Infof(ctx, "[Tool][DatabaseQuery] Retrieved %d rows with %d columns", len(results), len(columns))
	logger.Debugf(ctx, "[Tool][DatabaseQuery] Columns: %v", columns)

	// Log first few rows for debugging
	if len(results) > 0 {
		logger.Debugf(ctx, "[Tool][DatabaseQuery] First row sample:")
		for key, value := range results[0] {
			logger.Debugf(ctx, "[Tool][DatabaseQuery]   %s: %v", key, value)
		}
	}

	// Format output
	logger.Debugf(ctx, "[Tool][DatabaseQuery] Formatting query results...")
	output := t.formatQueryResults(columns, results, securedSQL)

	logger.Infof(ctx, "[Tool][DatabaseQuery] Execute completed successfully: %d rows returned", len(results))
	return &types.ToolResult{
		Success: true,
		Output:  output,
		Data: map[string]interface{}{
			"columns":      columns,
			"rows":         results,
			"row_count":    len(results),
			"query":        securedSQL,
			"tenant_id":    t.tenantID,
			"display_type": "database_query",
		},
	}, nil
}

// validateAndSecureSQL validates the SQL query and injects tenant_id conditions
func (t *DatabaseQueryTool) validateAndSecureSQL(sqlQuery string) (string, error) {
	// Normalize SQL: trim and convert to lowercase for analysis
	normalizedSQL := strings.TrimSpace(sqlQuery)
	lowerSQL := strings.ToLower(normalizedSQL)

	// 1. Check if it's a SELECT statement
	if !strings.HasPrefix(lowerSQL, "select") {
		return "", fmt.Errorf("only SELECT queries are allowed")
	}

	// 2. Check for dangerous keywords
	dangerousKeywords := []string{
		"drop", "delete", "insert", "update", "alter", "create",
		"truncate", "replace", "execute", "exec", "grant", "revoke",
	}
	for _, keyword := range dangerousKeywords {
		// Use word boundary to avoid false positives (e.g., "description" contains "script")
		pattern := fmt.Sprintf(`\b%s\b`, keyword)
		matched, _ := regexp.MatchString(pattern, lowerSQL)
		if matched {
			return "", fmt.Errorf("dangerous keyword detected: %s", keyword)
		}
	}

	// 3. Check for allowed tables
	allowedTables := []string{
		"tenants", "knowledge_bases", "knowledges", "sessions",
		"messages", "chunks", "embeddings", "models",
	}

	// Extract table names from FROM and JOIN clauses
	tablePattern := regexp.MustCompile(`(?i)\b(?:from|join)\s+([a-z_]+)(?:\s+as\s+[a-z_]+|\s+[a-z_]+)?`)
	matches := tablePattern.FindAllStringSubmatch(lowerSQL, -1)

	tablesInQuery := make(map[string]bool)
	for _, match := range matches {
		if len(match) > 1 {
			tableName := strings.ToLower(match[1])
			tablesInQuery[tableName] = true
		}
	}

	// Verify all tables are allowed
	for tableName := range tablesInQuery {
		allowed := false
		for _, allowedTable := range allowedTables {
			if tableName == allowedTable {
				allowed = true
				break
			}
		}
		if !allowed {
			return "", fmt.Errorf("table not allowed: %s", tableName)
		}
	}

	// 4. Inject tenant_id conditions for tables that have tenant_id
	tablesWithTenantID := map[string]bool{
		"tenants":         true,
		"knowledge_bases": true,
		"knowledges":      true,
		"sessions":        true,
		"chunks":          true,
	}

	// Build tenant_id injection
	securedSQL := normalizedSQL

	// Check if WHERE clause exists
	wherePattern := regexp.MustCompile(`(?i)\bwhere\b`)
	hasWhere := wherePattern.MatchString(securedSQL)

	// Find table aliases
	aliasPattern := regexp.MustCompile(`(?i)(?:from|join)\s+([a-z_]+)(?:\s+(?:as\s+)?([a-z_]+))?`)
	aliasMatches := aliasPattern.FindAllStringSubmatch(lowerSQL, -1)

	tableAliases := make(map[string]string) // table -> alias
	for _, match := range aliasMatches {
		if len(match) >= 3 && match[2] != "" {
			// Has explicit alias
			tableAliases[match[1]] = match[2]
		} else if len(match) >= 2 {
			// No alias, use table name itself
			tableAliases[match[1]] = match[1]
		}
	}

	// Build tenant_id conditions
	var tenantConditions []string
	for tableName := range tablesInQuery {
		if tablesWithTenantID[tableName] {
			alias := tableAliases[tableName]
			if alias == "" {
				alias = tableName
			}
			// Special handling for tenants table - use id instead of tenant_id
			if tableName == "tenants" {
				tenantConditions = append(tenantConditions, fmt.Sprintf("%s.id = %d", alias, t.tenantID))
			} else {
				tenantConditions = append(tenantConditions, fmt.Sprintf("%s.tenant_id = %d", alias, t.tenantID))
			}
		}
	}

	if len(tenantConditions) > 0 {
		tenantFilter := strings.Join(tenantConditions, " AND ")
		if hasWhere {
			// Add to existing WHERE clause
			securedSQL = wherePattern.ReplaceAllString(securedSQL, fmt.Sprintf("WHERE %s AND ", tenantFilter))
		} else {
			// Add new WHERE clause before ORDER BY, GROUP BY, LIMIT, etc.
			orderByPattern := regexp.MustCompile(`(?i)\b(group\s+by|order\s+by|limit|offset|having)\b`)
			if orderByPattern.MatchString(securedSQL) {
				securedSQL = orderByPattern.ReplaceAllStringFunc(securedSQL, func(match string) string {
					return fmt.Sprintf(" WHERE %s %s", tenantFilter, match)
				})
			} else {
				// Add WHERE clause at the end
				securedSQL = fmt.Sprintf("%s WHERE %s", securedSQL, tenantFilter)
			}
		}
	}

	return securedSQL, nil
}

// formatQueryResults formats query results into readable text
func (t *DatabaseQueryTool) formatQueryResults(
	columns []string,
	results []map[string]interface{},
	query string,
) string {
	output := "=== 查询结果 ===\n\n"
	output += fmt.Sprintf("执行的SQL: %s\n\n", query)
	output += fmt.Sprintf("返回 %d 行数据\n\n", len(results))

	if len(results) == 0 {
		output += "未找到匹配的记录。\n"
		return output
	}

	output += "=== 数据详情 ===\n\n"

	// Format each row
	for i, row := range results {
		output += fmt.Sprintf("--- 记录 #%d ---\n", i+1)
		for _, col := range columns {
			value := row[col]
			// Format the value
			var formattedValue string
			if value == nil {
				formattedValue = "<NULL>"
			} else if jsonData, err := json.Marshal(value); err == nil {
				// Check if it's a complex type
				switch v := value.(type) {
				case string:
					formattedValue = v
				case []byte:
					formattedValue = string(v)
				default:
					formattedValue = string(jsonData)
				}
			} else {
				formattedValue = fmt.Sprintf("%v", value)
			}

			output += fmt.Sprintf("  %s: %s\n", col, formattedValue)
		}
		output += "\n"
	}

	// Add summary statistics if applicable
	if len(results) > 10 {
		output += fmt.Sprintf("注意: 显示了前 %d 条记录，共 %d 条。建议使用 LIMIT 子句限制结果数量。\n", len(results), len(results))
	}

	return output
}
