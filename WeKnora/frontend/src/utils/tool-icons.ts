/**
 * Tool Icons Utility
 * Maps tool names and match types to icons for better UI display
 */

// Tool name to icon mapping
export const toolIcons: Record<string, string> = {
    multi_kb_search: '🔍',
    knowledge_search: '📚',
    grep_chunks: '🔎',
    get_chunk_detail: '📄',
    list_knowledge_bases: '📂',
    list_knowledge_chunks: '🧩',
    get_document_info: 'ℹ️',
    query_knowledge_graph: '🕸️',
    think: '💭',
    todo_write: '📋',
};

// Match type to icon mapping
export const matchTypeIcons: Record<string, string> = {
    '向量匹配': '🎯',
    '关键词匹配': '🔤',
    '相邻块匹配': '📌',
    '历史匹配': '📜',
    '父块匹配': '⬆️',
    '关系块匹配': '🔗',
    '图谱匹配': '🕸️',
};

// Get icon for a tool name
export function getToolIcon(toolName: string): string {
    return toolIcons[toolName] || '🛠️';
}

// Get icon for a match type
export function getMatchTypeIcon(matchType: string): string {
    return matchTypeIcons[matchType] || '📍';
}

// Get tool display name (user-friendly)
export function getToolDisplayName(toolName: string): string {
    const displayNames: Record<string, string> = {
        multi_kb_search: '跨库搜索',
        knowledge_search: '知识库搜索',
        grep_chunks: '文本模式搜索',
        get_chunk_detail: '获取片段详情',
        list_knowledge_chunks: '查看知识分块',
        list_knowledge_bases: '列出知识库',
        get_document_info: '获取文档信息',
        query_knowledge_graph: '查询知识图谱',
        think: '深度思考',
        todo_write: '制定计划',
    };
    return displayNames[toolName] || toolName;
}

