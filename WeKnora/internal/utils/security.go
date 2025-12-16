package utils

import (
	"html"
	"regexp"
	"strings"
	"unicode/utf8"
)

// XSS 防护相关正则表达式
var (
	// 匹配潜在的 XSS 攻击模式
	xssPatterns = []*regexp.Regexp{
		regexp.MustCompile(`(?i)<script[^>]*>.*?</script>`),
		regexp.MustCompile(`(?i)<iframe[^>]*>.*?</iframe>`),
		regexp.MustCompile(`(?i)<object[^>]*>.*?</object>`),
		regexp.MustCompile(`(?i)<embed[^>]*>.*?</embed>`),
		regexp.MustCompile(`(?i)<embed[^>]*>`),
		regexp.MustCompile(`(?i)<form[^>]*>.*?</form>`),
		regexp.MustCompile(`(?i)<input[^>]*>`),
		regexp.MustCompile(`(?i)<button[^>]*>.*?</button>`),
		regexp.MustCompile(`(?i)javascript:`),
		regexp.MustCompile(`(?i)vbscript:`),
		regexp.MustCompile(`(?i)onload\s*=`),
		regexp.MustCompile(`(?i)onerror\s*=`),
		regexp.MustCompile(`(?i)onclick\s*=`),
		regexp.MustCompile(`(?i)onmouseover\s*=`),
		regexp.MustCompile(`(?i)onfocus\s*=`),
		regexp.MustCompile(`(?i)onblur\s*=`),
	}
)

// SanitizeHTML 清理 HTML 内容，防止 XSS 攻击
func SanitizeHTML(input string) string {
	if input == "" {
		return ""
	}

	// 检查输入长度
	if len(input) > 10000 {
		input = input[:10000]
	}

	// 检查是否包含潜在的 XSS 攻击
	for _, pattern := range xssPatterns {
		if pattern.MatchString(input) {
			// 如果包含恶意内容，进行 HTML 转义
			return html.EscapeString(input)
		}
	}

	// 如果内容相对安全，返回原内容
	return input
}

// EscapeHTML 转义 HTML 特殊字符
func EscapeHTML(input string) string {
	if input == "" {
		return ""
	}
	return html.EscapeString(input)
}

// ValidateInput 验证用户输入
func ValidateInput(input string) (string, bool) {
	if input == "" {
		return "", true
	}

	// 检查长度
	if len(input) > 10000 {
		return "", false
	}

	// 检查是否包含控制字符
	for _, r := range input {
		if r < 32 && r != 9 && r != 10 && r != 13 {
			return "", false
		}
	}

	// 检查 UTF-8 有效性
	if !utf8.ValidString(input) {
		return "", false
	}

	// 检查是否包含潜在的 XSS 攻击
	for _, pattern := range xssPatterns {
		if pattern.MatchString(input) {
			return "", false
		}
	}

	return strings.TrimSpace(input), true
}

// IsValidURL 验证 URL 是否安全
func IsValidURL(url string) bool {
	if url == "" {
		return false
	}

	// 检查长度
	if len(url) > 2048 {
		return false
	}

	// 检查协议
	if !strings.HasPrefix(strings.ToLower(url), "http://") &&
		!strings.HasPrefix(strings.ToLower(url), "https://") {
		return false
	}

	// 检查是否包含恶意内容
	for _, pattern := range xssPatterns {
		if pattern.MatchString(url) {
			return false
		}
	}

	return true
}

// IsValidImageURL 验证图片 URL 是否安全
func IsValidImageURL(url string) bool {
	if !IsValidURL(url) {
		return false
	}

	// 检查是否为图片文件
	imageExtensions := []string{".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}
	lowerURL := strings.ToLower(url)

	for _, ext := range imageExtensions {
		if strings.Contains(lowerURL, ext) {
			return true
		}
	}

	return false
}

// CleanMarkdown 清理 Markdown 内容
func CleanMarkdown(input string) string {
	if input == "" {
		return ""
	}

	// 移除潜在的恶意脚本
	cleaned := input
	for _, pattern := range xssPatterns {
		cleaned = pattern.ReplaceAllString(cleaned, "")
	}

	return cleaned
}

// SanitizeForDisplay 为显示清理内容
func SanitizeForDisplay(input string) string {
	if input == "" {
		return ""
	}

	// 首先清理 Markdown
	cleaned := CleanMarkdown(input)

	// 然后进行 HTML 转义
	escaped := html.EscapeString(cleaned)

	return escaped
}

// SanitizeForLog 清理日志输入,防止日志注入攻击
// 日志注入攻击是指攻击者通过在输入中插入换行符和其他控制字符,
// 伪造日志条目,可能导致日志分析工具误判或隐藏恶意活动
func SanitizeForLog(input string) string {
	if input == "" {
		return ""
	}

	// 替换换行符(LF, CR, CRLF)为空格,防止日志注入
	sanitized := strings.ReplaceAll(input, "\n", " ")
	sanitized = strings.ReplaceAll(sanitized, "\r", " ")

	// 替换制表符为空格
	sanitized = strings.ReplaceAll(sanitized, "\t", " ")

	// 移除其他控制字符(ASCII 0-31,除了空格已处理的)
	var builder strings.Builder
	for _, r := range sanitized {
		// 保留可打印字符和常用Unicode字符
		if r >= 32 || r == ' ' {
			builder.WriteRune(r)
		}
	}

	sanitized = builder.String()

	// 限制长度,防止日志溢出
	if len(sanitized) > 1000 {
		sanitized = sanitized[:1000] + "...[truncated]"
	}

	return sanitized
}

// SanitizeForLogArray 清理日志输入数组,防止日志注入攻击
func SanitizeForLogArray(input []string) []string {
	if len(input) == 0 {
		return []string{}
	}

	sanitized := make([]string, 0, len(input))
	for _, item := range input {
		sanitized = append(sanitized, SanitizeForLog(item))
	}

	return sanitized
}
