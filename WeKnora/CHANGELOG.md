# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2025-12-08

### 🚀 New Features
- **NEW**: Qdrant Vector Database Support
  - Full integration with Qdrant as retriever engine
  - Support for both vector similarity search and full-text keyword search
  - Dynamic collection creation based on embedding dimensions (e.g., `weknora_embeddings_768`)
  - Multilingual tokenizer support for Chinese/Japanese/Korean text search
  - Professional Chinese word segmentation using jieba for keyword queries

### ⚡ Infrastructure Improvements
- **IMPROVED**: Docker Compose Profile Management
  - Added profiles for optional services: `minio`, `qdrant`, `neo4j`, `jaeger`, `full`
  - Enhanced `dev.sh` script with `--minio`, `--qdrant`, `--neo4j`, `--jaeger`, `--full` flags
  - Pinned Qdrant Docker image version to `v1.16.2` for stability
- **IMPROVED**: Database Migration System
  - Added automatic dirty state recovery for failed migrations
  - Added Neo4j connection retry mechanism with exponential backoff
  - Improved migration error handling and logging
- **IMPROVED**: Retriever Engine Configuration
  - Retriever engines now auto-configured from `RETRIEVE_DRIVER` environment variable
  - No longer required to write retriever config during user registration
  - Added `GetEffectiveEngines()` method for dynamic engine resolution
  - Centralized engine mapping in `types/tenant.go`

### 🐛 Bug Fixes
- **FIXED**: Qdrant keyword search returning empty results for Chinese queries
- **FIXED**: Image URL validation logic simplified for better compatibility

### 📚 Documentation
- Added Qdrant configuration examples in docker-compose files

## [0.2.0] - 2025-12-05

### 🚀 Major Features
- **NEW**: ReACT Agent Mode
  - Added ReACT Agent mode that can use built-in tools to retrieve knowledge bases
  - Support for calling user-configured MCP tools and web search tools to access external services
  - Multiple iterations and reflection to provide comprehensive summary reports
  - Cross-knowledge base retrieval support, allowing selection of multiple knowledge bases
- **NEW**: Model Management System
  - Centralized model configuration
  - Added model selection in knowledge base settings page
  - Built-in model sharing functionality across multiple tenants
  - Tenants can use shared models but are restricted from editing or viewing model details
- **NEW**: Multi-Type Knowledge Base Support
  - Support for creating FAQ and document knowledge base types
  - Folder import functionality
  - URL import functionality
  - Tag management system
  - Online knowledge entry capability
- **NEW**: FAQ Knowledge Base
  - New FAQ-type knowledge base
  - Batch import and batch delete functionality
  - Online FAQ entry
  - Online FAQ testing capability
- **NEW**: Conversation Strategy Configuration
  - Support for configuring Agent models and normal mode models
  - Configurable retrieval thresholds
  - Online Prompt configuration
  - Precise control over multi-turn conversation behavior and retrieval execution methods
- **NEW**: Web Search Integration
  - Support for extensible web search engines
  - Built-in DuckDuckGo search engine
- **NEW**: MCP Tool Integration
  - Support for extending Agent capabilities through MCP
  - Built-in uvx and npx MCP launcher tools
  - Support for three transport methods: Stdio, HTTP Streamable, and SSE

### 🎨 UI/UX Improvements
- **REDESIGNED**: Conversation interface with Agent mode/normal mode switching
  - Added Agent mode/normal mode toggle in conversation input box
  - Support for enabling/disabling web search
  - Support for selecting conversation models
- **REDESIGNED**: Login page UI adjustments
- **ENHANCED**: Session list with time-ordered grouping
- **NEW**: Quick Actions area for unified UI visual effects
- **IMPROVED**: Knowledge base list cards
  - Display knowledge base type, knowledge count, build status
  - Show advanced settings capabilities
- **NEW**: Breadcrumb navigation in FAQ and document list pages
  - Quick navigation and knowledge base switching
- **ENHANCED**: Knowledge base settings in document list page
- **REDESIGNED**: Knowledge base settings page
  - Separate configuration for knowledge base type, models, chunking methods, and advanced settings
- **NEW**: Global settings page for permissions
  - Configure models, web search, MCP services, and Agent mode
- **IMPROVED**: Chunk details page display
- **NEW**: Knowledge classification and tagging support
- **ENHANCED**: Conversation flow page with tool call execution process display

### ⚡ Infrastructure Upgrades
- **NEW**: MQ-based async task management
  - Introduced MQ for async task state maintenance
  - Ensures task integrity even after service abnormal restart
- **NEW**: Automatic database migration
  - Support for automatic database schema and data migration during version upgrades
- **NEW**: Fast development mode
  - Added docker-compose.dev.yml file for quick development environment startup
  - Improved development workflow efficiency
- **IMPROVED**: Log structure optimization
- **NEW**: Event subscription and publishing mechanism
  - Support for event handling at various steps in user query processing flow

### 🐛 Bug Fixes
- Various bug fixes and stability improvements

### 📚 Documentation Updates
- Updated README files with v0.2.0 highlights (English, Chinese, Japanese)
- Added latest updates section in all README files
- Updated architecture diagrams and feature matrices
## [0.1.6] - 2025-11-24

### Document Parser Enhancements
- NEW: Added CSV, XLSX, XLS file parsing support (spreadsheet processing, tabular data extraction)
- NEW: Web page parser (dedicated class, optimized web image encoding, improved dependency management)

### Document Processing Improvements
- NEW: MarkdownTableUtil (reduced whitespace, improved table readability/consistency)
- NEW: Document model class (structured models for type safety, optimized config/parsing logic)
- UPGRADED: Docx2Parser (enhanced timeout handling, better image processing, optimized OCR backend)

### Internationalization
- NEW: English/Russian multi-language support (vue-i18n integration, translated UI/text/errors, multilingual docs for knowledge graph/MCP config)

### Bug Fixes
- Fixed menu component integration issues
- Fixed Darwin (macOS) memory check regex error (resolved empty output)
- Fixed model availability check (unified logic, auto ":latest" tag, prevented duplicate pull calls)
- Fixed Docker Compose security vulnerability (addressed writable filesystem issue)

### Refactoring & Optimization
- Refactored parser logging/API checks (simplified exception handling, better error reporting)
- Refactored chunk processing (removed redundant header handling, updated examples)
- Refactored module organization (docreader structure, proto/client imports, Docker config, absolute imports)

### Documentation Updates
- Updated API Key acquisition docs (web registration + account page retrieval)
- Updated Docker Compose setup guide (comprehensive instructions, config adjustments)
- Updated multilingual docs (added knowledge graph/MCP config guides, directory structure)
- Removed deprecated hybrid search API docs

### Code Cleanup
- Removed redundant Docker build parameters
- Updated .gitignore rules
- Optimized import statements/type hints
- Cleaned redundant logging/comments

### CI/CD Improvements
- Added new CI/CD trigger branches
- Added build concurrency control
- Added disk space cleanup automation

## [0.1.5] - 2025-10-20

### Features & Enhancements
- Added multi-knowledgebases operation support and management (UI & backend logic)
- Enhanced tenant information management: New tenant page with user-friendly storage quota and usage rate display (see TenantInfo.vue)
- Initialization Wizard improvements: Stricter form validation, VLM/OpenAI compatible URL verification, and multimodal file upload preview & validation (see InitializationContent.vue)
- Backend: API Key automatic generation and update logic (see types.Tenant & tenantService.UpdateTenant)

### UI / UX
- Restructured settings page and initialization page layouts; optimized button states, loading states, and prompt messages; improved upload/preview experience
- Enhanced menu component: Multi-knowledgebase switching and pre-upload validation logic (see menu.vue)
- Hidden/protected sensitive information (e.g., API Keys) and added copy interaction prompts (see TenantInfo.vue)

### Security Fixes
- Fixed potential frontend XSS vulnerabilities; enhanced input validation and Content Security Policy
- Hidden API Keys in UI and improved copy behavior prompts to strengthen information leakage protection

### Bug Fixes
- Resolved OCR/AVX support-related issues and image parsing concurrency errors
- Fixed frontend routing/login redirection issues and file download content errors
- Fixed docreader service health check and model prefetching issues

### DevOps / Building
- Improved image building scripts: Enhanced platform/architecture detection (amd64 / arm64) and injected version information during build (see get_version.sh & build_images.sh)
- Refined Makefile and build process to facilitate CI injection of LDFLAGS (see Makefile)
- Improved usage and documentation for scripts and migration tools (migrate) (see migrate.sh)

### Documentation
- Updated README and multilingual documentation (EN/CN/JA) along with release/CHANGELOG (see CHANGELOG.md & README.md for details)
- Added MCP server usage instructions and installation guide (see mcp-server/INSTALL.md)

### Developer / Internal API Changes (For Reference)
- New/updated backend system information response structure: handler.GetSystemInfoResponse
- Tenant data structure and JSON storage fields: types.Tenant

## [0.1.4] - 2025-09-17

### 🚀 Major Features
- **NEW**: Multi-knowledgebases operation support
  - Added comprehensive multi-knowledgebase management functionality
  - Implemented multi-data source search engine configuration and optimization logic
  - Enhanced knowledge base switching and management in UI
- **NEW**: Enhanced tenant information management
  - Added dedicated tenant information page
  - Improved user and tenant management capabilities

### 🎨 UI/UX Improvements
- **REDESIGNED**: Settings page with improved layout and functionality
- **ENHANCED**: Menu component with multi-knowledgebase support
- **IMPROVED**: Initialization configuration page structure
- **OPTIMIZED**: Login page and authentication flow

### 🔒 Security Fixes
- **FIXED**: XSS attack vulnerabilities in thinking component
- **FIXED**: Content Security Policy (CSP) errors
- **ENHANCED**: Frontend security measures and input sanitization

### 🐛 Bug Fixes
- **FIXED**: Login direct page navigation issues
- **FIXED**: App LLM model check logic
- **FIXED**: Version script functionality
- **FIXED**: File download content errors
- **IMPROVED**: Document content component display

### 🧹 Code Cleanup
- **REMOVED**: Test data functionality and related APIs
- **SIMPLIFIED**: Initialization configuration components
- **CLEANED**: Redundant UI components and unused code


## [0.1.3] - 2025-09-16

### 🔒 Security Features
- **NEW**: Added login authentication functionality to enhance system security
- Implemented user authentication and authorization mechanisms
- Added session management and access control
- Fixed XSS attack vulnerabilities in frontend components

### 📚 Documentation Updates
- Added security notices in all README files (English, Chinese, Japanese)
- Updated deployment recommendations emphasizing internal/private network deployment
- Enhanced security guidelines to prevent information leakage risks
- Fixed documentation spelling issues

### 🛡️ Security Improvements
- Hide API keys in UI for security purposes
- Enhanced input sanitization and XSS protection
- Added comprehensive security utilities

### 🐛 Bug Fixes
- Fixed OCR AVX support issues
- Improved frontend health check dependencies
- Enhanced Docker binary downloads for target architecture
- Fixed COS file service initialization parameters and URL processing logic

### 🚀 Features & Enhancements
- Improved application and docreader log output
- Enhanced frontend routing and authentication flow
- Added comprehensive user management system
- Improved initialization configuration handling

### 🛡️ Security Recommendations
- Deploy WeKnora services in internal/private network environments
- Avoid direct exposure to public internet
- Configure proper firewall rules and access controls
- Regular updates for security patches and improvements

## [0.1.2] - 2025-09-10

- Fixed health check implementation for docreader service
- Improved query handling for empty queries
- Enhanced knowledge base column value update methods
- Optimized logging throughout the application
- Added process parsing documentation for markdown files
- Fixed OCR model pre-fetching in Docker containers
- Resolved image parser concurrency errors
- Added support for modifying listening port configuration

## [0.1.0] - 2025-09-08

- Initial public release of WeKnora.
- Web UI for knowledge upload, chat, configuration, and settings.
- RAG pipeline with chunking, embedding, retrieval, reranking, and generation.
- Initialization wizard for configuring models (LLM, embedding, rerank, retriever).
- Support for local Ollama and remote API models.
- Vector backends: PostgreSQL (pgvector), Elasticsearch; GraphRAG support.
- End-to-end evaluation utilities and metrics.
- Docker Compose for quick startup and service orchestration.
- MCP server support for integrating with MCP-compatible clients.

[0.2.1]: https://github.com/Tencent/WeKnora/tree/v0.2.1
[0.2.0]: https://github.com/Tencent/WeKnora/tree/v0.2.0
[0.1.4]: https://github.com/Tencent/WeKnora/tree/v0.1.4
[0.1.3]: https://github.com/Tencent/WeKnora/tree/v0.1.3
[0.1.2]: https://github.com/Tencent/WeKnora/tree/v0.1.2
[0.1.0]: https://github.com/Tencent/WeKnora/tree/v0.1.0
