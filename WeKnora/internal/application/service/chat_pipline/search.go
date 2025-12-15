package chatpipline

import (
	"context"
	"fmt"
	"regexp"
	"strings"
	"sync"
	"unicode"

	"github.com/Tencent/WeKnora/internal/config"
	"github.com/Tencent/WeKnora/internal/logger"
	"github.com/Tencent/WeKnora/internal/searchutil"
	"github.com/Tencent/WeKnora/internal/types"
	"github.com/Tencent/WeKnora/internal/types/interfaces"
)

// PluginSearch implements search functionality for chat pipeline
type PluginSearch struct {
	knowledgeBaseService interfaces.KnowledgeBaseService
	knowledgeService     interfaces.KnowledgeService
	config               *config.Config
	webSearchService     interfaces.WebSearchService
	tenantService        interfaces.TenantService
	sessionService       interfaces.SessionService
}

func NewPluginSearch(eventManager *EventManager,
	knowledgeBaseService interfaces.KnowledgeBaseService,
	knowledgeService interfaces.KnowledgeService,
	config *config.Config,
	webSearchService interfaces.WebSearchService,
	tenantService interfaces.TenantService,
	sessionService interfaces.SessionService,
) *PluginSearch {
	res := &PluginSearch{
		knowledgeBaseService: knowledgeBaseService,
		knowledgeService:     knowledgeService,
		config:               config,
		webSearchService:     webSearchService,
		tenantService:        tenantService,
		sessionService:       sessionService,
	}
	eventManager.Register(res)
	return res
}

// ActivationEvents returns the event types this plugin handles
func (p *PluginSearch) ActivationEvents() []types.EventType {
	return []types.EventType{types.CHUNK_SEARCH}
}

// OnEvent handles search events in the chat pipeline
func (p *PluginSearch) OnEvent(ctx context.Context,
	eventType types.EventType, chatManage *types.ChatManage, next func() *PluginError,
) *PluginError {
	// Get knowledge base IDs list
	knowledgeBaseIDs := chatManage.KnowledgeBaseIDs
	if len(knowledgeBaseIDs) == 0 && chatManage.KnowledgeBaseID != "" {
		// Fall back to single knowledge base
		knowledgeBaseIDs = []string{chatManage.KnowledgeBaseID}
		pipelineInfo(ctx, "Search", "fallback_kb", map[string]interface{}{
			"session_id": chatManage.SessionID,
			"kb_id":      chatManage.KnowledgeBaseID,
		})
	}

	if len(knowledgeBaseIDs) == 0 {
		pipelineError(ctx, "Search", "kb_not_found", map[string]interface{}{
			"session_id": chatManage.SessionID,
		})
		return ErrSearch.WithError(nil)
	}

	pipelineInfo(ctx, "Search", "input", map[string]interface{}{
		"session_id":    chatManage.SessionID,
		"rewrite_query": chatManage.RewriteQuery,
		"kb_ids":        strings.Join(knowledgeBaseIDs, ","),
		"tenant_id":     chatManage.TenantID,
		"web_enabled":   chatManage.WebSearchEnabled,
	})

	// Run KB search and web search concurrently
	pipelineInfo(ctx, "Search", "plan", map[string]interface{}{
		"kb_count":          len(knowledgeBaseIDs),
		"embedding_top_k":   chatManage.EmbeddingTopK,
		"vector_threshold":  chatManage.VectorThreshold,
		"keyword_threshold": chatManage.KeywordThreshold,
	})
	var wg sync.WaitGroup
	var mu sync.Mutex
	allResults := make([]*types.SearchResult, 0)

	wg.Add(2)
	// Goroutine 1: Knowledge base search (rewrite + processed)
	go func() {
		defer wg.Done()
		kbResults := p.searchKnowledgeBases(ctx, knowledgeBaseIDs, chatManage)
		if len(kbResults) > 0 {
			mu.Lock()
			allResults = append(allResults, kbResults...)
			mu.Unlock()
		}
	}()

	// Goroutine 2: Web search (if enabled)
	go func() {
		defer wg.Done()
		webResults := p.searchWebIfEnabled(ctx, chatManage)
		if len(webResults) > 0 {
			mu.Lock()
			allResults = append(allResults, webResults...)
			mu.Unlock()
		}
	}()

	wg.Wait()

	chatManage.SearchResult = allResults

	// Log all search results with scores before any processing
	for i, r := range chatManage.SearchResult {
		pipelineInfo(ctx, "Search", "result_score_before_normalize", map[string]interface{}{
			"index":      i,
			"chunk_id":   r.ID,
			"score":      fmt.Sprintf("%.4f", r.Score),
			"match_type": r.MatchType,
		})
	}

	// If recall is low, attempt query expansion with keyword-focused search
	if chatManage.EnableQueryExpansion && len(chatManage.SearchResult) < max(1, chatManage.EmbeddingTopK/2) {
		pipelineInfo(ctx, "Search", "recall_low", map[string]interface{}{
			"current":   len(chatManage.SearchResult),
			"threshold": chatManage.EmbeddingTopK / 2,
		})
		expansions := p.expandQueries(ctx, chatManage)
		if len(expansions) > 0 {
			pipelineInfo(ctx, "Search", "expansion_start", map[string]interface{}{
				"variants": len(expansions),
			})
			expTopK := max(chatManage.EmbeddingTopK*2, chatManage.RerankTopK*2)
			expKwTh := chatManage.KeywordThreshold * 0.8
			// Concurrent expansion retrieval across queries and KBs
			expResults := make([]*types.SearchResult, 0, expTopK*len(expansions))
			var muExp sync.Mutex
			var wgExp sync.WaitGroup
			jobs := len(expansions) * len(knowledgeBaseIDs)
			capSem := 16
			if jobs < capSem {
				capSem = jobs
			}
			if capSem <= 0 {
				capSem = 1
			}
			sem := make(chan struct{}, capSem)
			pipelineInfo(ctx, "Search", "expansion_concurrency", map[string]interface{}{
				"jobs": jobs,
				"cap":  capSem,
			})
			for _, q := range expansions {
				for _, kbID := range knowledgeBaseIDs {
					wgExp.Add(1)
					go func(q string, kbID string) {
						defer wgExp.Done()
						sem <- struct{}{}
						defer func() { <-sem }()
						paramsExp := types.SearchParams{
							QueryText:            q,
							VectorThreshold:      chatManage.VectorThreshold,
							KeywordThreshold:     expKwTh,
							MatchCount:           expTopK,
							DisableVectorMatch:   true,
							DisableKeywordsMatch: false,
						}
						res, err := p.knowledgeBaseService.HybridSearch(ctx, kbID, paramsExp)
						if err != nil {
							pipelineWarn(ctx, "Search", "expansion_error", map[string]interface{}{
								"kb_id": kbID,
								"error": err.Error(),
							})
							return
						}
						if len(res) > 0 {
							pipelineInfo(ctx, "Search", "expansion_hits", map[string]interface{}{
								"kb_id": kbID,
								"query": q,
								"hits":  len(res),
							})
							muExp.Lock()
							expResults = append(expResults, res...)
							muExp.Unlock()
						}
					}(q, kbID)
				}
			}
			wgExp.Wait()
			if len(expResults) > 0 {
				// Scores already normalized in HybridSearch
				pipelineInfo(ctx, "Search", "expansion_done", map[string]interface{}{
					"added": len(expResults),
				})
				chatManage.SearchResult = append(chatManage.SearchResult, expResults...)
			}
		}
	}

	// Add relevant results from chat history
	historyResult := p.getSearchResultFromHistory(chatManage)
	if historyResult != nil {
		pipelineInfo(ctx, "Search", "history_hits", map[string]interface{}{
			"session_id":   chatManage.SessionID,
			"history_hits": len(historyResult),
		})
		chatManage.SearchResult = append(chatManage.SearchResult, historyResult...)
	}

	// Remove duplicate results
	before := len(chatManage.SearchResult)
	chatManage.SearchResult = removeDuplicateResults(chatManage.SearchResult)
	pipelineInfo(ctx, "Search", "dedup_summary", map[string]interface{}{
		"before": before,
		"after":  len(chatManage.SearchResult),
	})

	// Log final scores after all processing
	for i, r := range chatManage.SearchResult {
		pipelineInfo(ctx, "Search", "final_score", map[string]interface{}{
			"index":      i,
			"chunk_id":   r.ID,
			"score":      fmt.Sprintf("%.4f", r.Score),
			"match_type": r.MatchType,
		})
	}

	// Return if we have results
	if len(chatManage.SearchResult) != 0 {
		pipelineInfo(ctx, "Search", "output", map[string]interface{}{
			"session_id":   chatManage.SessionID,
			"result_count": len(chatManage.SearchResult),
		})
		return next()
	}
	pipelineWarn(ctx, "Search", "output", map[string]interface{}{
		"session_id":   chatManage.SessionID,
		"result_count": 0,
	})
	return ErrSearchNothing
}

// getSearchResultFromHistory retrieves relevant knowledge references from chat history
func (p *PluginSearch) getSearchResultFromHistory(chatManage *types.ChatManage) []*types.SearchResult {
	if len(chatManage.History) == 0 {
		return nil
	}
	// Search history in reverse chronological order
	for i := len(chatManage.History) - 1; i >= 0; i-- {
		if len(chatManage.History[i].KnowledgeReferences) > 0 {
			// Mark all references as history matches
			for _, reference := range chatManage.History[i].KnowledgeReferences {
				reference.MatchType = types.MatchTypeHistory
			}
			return chatManage.History[i].KnowledgeReferences
		}
	}
	return nil
}

func removeDuplicateResults(results []*types.SearchResult) []*types.SearchResult {
	seen := make(map[string]bool)
	contentSig := make(map[string]string) // sig -> first chunk ID
	var uniqueResults []*types.SearchResult
	for _, r := range results {
		keys := []string{r.ID}
		if r.ParentChunkID != "" {
			keys = append(keys, "parent:"+r.ParentChunkID)
		}
		dup := false
		dupKey := ""
		for _, k := range keys {
			if seen[k] {
				dup = true
				dupKey = k
				break
			}
		}
		if dup {
			logger.Debugf(context.Background(), "Dedup: chunk %s removed due to key: %s", r.ID, dupKey)
			continue
		}
		sig := buildContentSignature(r.Content)
		if sig != "" {
			if firstChunk, exists := contentSig[sig]; exists {
				logger.Debugf(context.Background(), "Dedup: chunk %s removed due to content signature (dup of %s, sig prefix: %.50s...)", r.ID, firstChunk, sig)
				continue
			}
			contentSig[sig] = r.ID
		}
		for _, k := range keys {
			seen[k] = true
		}
		uniqueResults = append(uniqueResults, r)
	}
	return uniqueResults
}

func buildContentSignature(content string) string {
	return searchutil.BuildContentSignature(content)
}

// searchKnowledgeBases performs KB searches across KB IDs using RewriteQuery only
func (p *PluginSearch) searchKnowledgeBases(
	ctx context.Context,
	knowledgeBaseIDs []string,
	chatManage *types.ChatManage,
) []*types.SearchResult {
	// Build params for rewrite query
	baseParams := types.SearchParams{
		QueryText:        strings.TrimSpace(chatManage.RewriteQuery),
		VectorThreshold:  chatManage.VectorThreshold,
		KeywordThreshold: chatManage.KeywordThreshold,
		MatchCount:       chatManage.EmbeddingTopK,
	}

	var wg sync.WaitGroup
	var mu sync.Mutex
	var results []*types.SearchResult

	// Search with rewrite query only (removed duplicate ProcessedQuery search)
	for _, kbID := range knowledgeBaseIDs {
		wg.Add(1)
		go func(knowledgeBaseID string) {
			defer wg.Done()
			res, err := p.knowledgeBaseService.HybridSearch(ctx, knowledgeBaseID, baseParams)
			if err != nil {
				pipelineWarn(ctx, "Search", "kb_search_error", map[string]interface{}{
					"kb_id": knowledgeBaseID,
					"query": baseParams.QueryText,
					"error": err.Error(),
				})
				return
			}
			pipelineInfo(ctx, "Search", "kb_result", map[string]interface{}{
				"kb_id":     knowledgeBaseID,
				"hit_count": len(res),
			})
			mu.Lock()
			results = append(results, res...)
			mu.Unlock()
		}(kbID)
	}

	wg.Wait()

	pipelineInfo(ctx, "Search", "kb_result_summary", map[string]interface{}{
		"total_hits": len(results),
	})
	return results
}

// searchWebIfEnabled executes web search when enabled and returns converted results
func (p *PluginSearch) searchWebIfEnabled(ctx context.Context, chatManage *types.ChatManage) []*types.SearchResult {
	if !chatManage.WebSearchEnabled || p.webSearchService == nil || p.tenantService == nil || chatManage.TenantID <= 0 {
		return nil
	}
	tenant := ctx.Value(types.TenantInfoContextKey).(*types.Tenant)
	if tenant == nil || tenant.WebSearchConfig == nil || tenant.WebSearchConfig.Provider == "" {
		pipelineWarn(ctx, "Search", "web_config_missing", map[string]interface{}{
			"tenant_id": chatManage.TenantID,
		})
		return nil
	}

	pipelineInfo(ctx, "Search", "web_request", map[string]interface{}{
		"tenant_id": chatManage.TenantID,
		"provider":  tenant.WebSearchConfig.Provider,
	})
	webResults, err := p.webSearchService.Search(ctx, tenant.WebSearchConfig, chatManage.RewriteQuery)
	if err != nil {
		pipelineWarn(ctx, "Search", "web_search_error", map[string]interface{}{
			"tenant_id": chatManage.TenantID,
			"error":     err.Error(),
		})
		return nil
	}
	// Build questions using RewriteQuery only
	questions := []string{strings.TrimSpace(chatManage.RewriteQuery)}
	// Load session-scoped temp KB state from Redis using SessionService
	tempKBID, seen, ids := p.sessionService.GetWebSearchTempKBState(ctx, chatManage.SessionID)
	compressed, kbID, newSeen, newIDs, err := p.webSearchService.CompressWithRAG(
		ctx, chatManage.SessionID, tempKBID, questions, webResults, tenant.WebSearchConfig,
		p.knowledgeBaseService, p.knowledgeService, seen, ids,
	)
	if err != nil {
		pipelineWarn(ctx, "Search", "web_compress_error", map[string]interface{}{
			"error": err.Error(),
		})
	} else {
		webResults = compressed
		// Persist temp KB state back into Redis using SessionService
		p.sessionService.SaveWebSearchTempKBState(ctx, chatManage.SessionID, kbID, newSeen, newIDs)
	}
	res := searchutil.ConvertWebSearchResults(webResults)
	pipelineInfo(ctx, "Search", "web_hits", map[string]interface{}{
		"hit_count": len(res),
	})
	return res
}

// expandQueries generates query variants locally without LLM to improve keyword recall
// Uses simple techniques: word reordering, stopword removal, key phrase extraction
func (p *PluginSearch) expandQueries(ctx context.Context, chatManage *types.ChatManage) []string {
	query := strings.TrimSpace(chatManage.RewriteQuery)
	if query == "" {
		return nil
	}

	expansions := make([]string, 0, 5)
	seen := make(map[string]struct{})
	seen[strings.ToLower(query)] = struct{}{}
	if q := strings.ToLower(chatManage.Query); q != "" {
		seen[q] = struct{}{}
	}

	addIfNew := func(s string) {
		s = strings.TrimSpace(s)
		if s == "" || len(s) < 3 {
			return
		}
		key := strings.ToLower(s)
		if _, ok := seen[key]; ok {
			return
		}
		seen[key] = struct{}{}
		expansions = append(expansions, s)
	}

	// 1. Remove common stopwords and create keyword-only variant
	keywords := extractKeywords(query)
	if len(keywords) >= 2 {
		addIfNew(strings.Join(keywords, " "))
	}

	// 2. Extract quoted phrases or key segments
	phrases := extractPhrases(query)
	for _, phrase := range phrases {
		addIfNew(phrase)
	}

	// 3. Split by common delimiters and use longest segment
	segments := splitByDelimiters(query)
	for _, seg := range segments {
		if len(seg) > 5 {
			addIfNew(seg)
		}
	}

	// 4. Remove question words (什么/如何/怎么/为什么/哪个 etc.)
	cleaned := removeQuestionWords(query)
	if cleaned != query {
		addIfNew(cleaned)
	}

	// Limit to 5 expansions
	if len(expansions) > 5 {
		expansions = expansions[:5]
	}

	pipelineInfo(ctx, "Search", "local_expansion_result", map[string]interface{}{
		"variants": len(expansions),
	})
	return expansions
}

// Common Chinese and English stopwords
var stopwords = map[string]struct{}{
	"的": {}, "是": {}, "在": {}, "了": {}, "和": {}, "与": {}, "或": {},
	"a": {}, "an": {}, "the": {}, "is": {}, "are": {}, "was": {}, "were": {},
	"be": {}, "been": {}, "being": {}, "have": {}, "has": {}, "had": {},
	"do": {}, "does": {}, "did": {}, "will": {}, "would": {}, "could": {},
	"should": {}, "may": {}, "might": {}, "must": {}, "can": {},
	"to": {}, "of": {}, "in": {}, "for": {}, "on": {}, "with": {}, "at": {},
	"by": {}, "from": {}, "as": {}, "into": {}, "through": {}, "about": {},
	"what": {}, "how": {}, "why": {}, "when": {}, "where": {}, "which": {},
	"who": {}, "whom": {}, "whose": {},
}

// Question words in Chinese
var questionWords = regexp.MustCompile(`^(什么是|什么|如何|怎么|怎样|为什么|为何|哪个|哪些|谁|何时|何地|请问|请告诉我|帮我|我想知道|我想了解)`)

func extractKeywords(text string) []string {
	words := tokenize(text)
	keywords := make([]string, 0, len(words))
	for _, w := range words {
		lower := strings.ToLower(w)
		if _, isStop := stopwords[lower]; !isStop && len(w) > 1 {
			keywords = append(keywords, w)
		}
	}
	return keywords
}

func extractPhrases(text string) []string {
	// Extract quoted content
	var phrases []string
	re := regexp.MustCompile(`["'"'「」『』]([^"'"'「」『』]+)["'"'「」『』]`)
	matches := re.FindAllStringSubmatch(text, -1)
	for _, m := range matches {
		if len(m) > 1 && len(m[1]) > 2 {
			phrases = append(phrases, m[1])
		}
	}
	return phrases
}

func splitByDelimiters(text string) []string {
	// Split by common delimiters
	re := regexp.MustCompile(`[,，;；、。！？!?\s]+`)
	parts := re.Split(text, -1)
	var result []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

func removeQuestionWords(text string) string {
	return strings.TrimSpace(questionWords.ReplaceAllString(text, ""))
}

func tokenize(text string) []string {
	var tokens []string
	var current strings.Builder

	for _, r := range text {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			current.WriteRune(r)
		} else if unicode.Is(unicode.Han, r) {
			// Flush current token
			if current.Len() > 0 {
				tokens = append(tokens, current.String())
				current.Reset()
			}
			// Chinese character as single token
			tokens = append(tokens, string(r))
		} else {
			// Delimiter
			if current.Len() > 0 {
				tokens = append(tokens, current.String())
				current.Reset()
			}
		}
	}
	if current.Len() > 0 {
		tokens = append(tokens, current.String())
	}
	return tokens
}
