# Contributing to AmaniQuery

Thank you for your interest in contributing to AmaniQuery! This document provides guidelines and information for contributors.

## Table of Contents

- [About AmaniQuery](#about-amaniquery)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## About AmaniQuery

AmaniQuery is an AI-powered legal intelligence platform that democratizes access to Kenyan legal information. It combines:

- **Constitutional Law Analysis**: Deep analysis of Kenya's constitution with AI-powered alignment checking
- **Parliamentary Intelligence**: Real-time access to parliamentary proceedings and bills
- **News Integration**: Factual news analysis with sentiment tracking
- **RAG Technology**: Retrieval-Augmented Generation for accurate, verifiable answers

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- Git
- PostgreSQL (for metadata storage)
- ChromaDB (for vector storage)

### Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/Benaah/amaniquery.git
   cd amaniquery
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your API keys and configuration

   # Initialize the database
   python -m Module3_NiruDB.populate_db
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Run the Application**
   ```bash
   # Terminal 1: Start the backend
   python -m Module4_NiruAPI.api

   # Terminal 2: Start the frontend (already running from step 3)
   # The frontend will be available at http://localhost:3000
   ```

## Development Setup

### Environment Configuration

Create a `.env` file in the root directory:

```env
# LLM Configuration
LLM_PROVIDER=moonshot
DEFAULT_MODEL=moonshot-v1-8k
MOONSHOT_API_KEY=your_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/amaniquery
CHROMA_DB_PATH=./chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Africa's Talking (for SMS)
AT_USERNAME=your_username
AT_API_KEY=your_api_key

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Database Setup

1. **PostgreSQL Setup**
   ```sql
   CREATE DATABASE amaniquery;
   CREATE USER amaniquery_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE amaniquery TO amaniquery_user;
   ```

2. **ChromaDB Setup**
   ```python
   # ChromaDB will be automatically initialized when the application starts
   # Data will be stored in the CHROMA_DB_PATH directory
   ```

## Project Structure

```
AmaniQuery/
├── Module1_NiruSpider/          # Web scraping and data collection
│   ├── crawl_all.py            # Main crawling orchestrator
│   ├── scrapy.cfg              # Scrapy configuration
│   └── niruspider/
│       ├── spiders/            # Individual spider implementations
│       └── pipelines.py        # Data processing pipelines
├── Module2_NiruParser/         # Document parsing and processing
│   ├── process_all.py          # Main processing script
│   ├── chunkers/               # Text chunking strategies
│   ├── cleaners/               # Text cleaning utilities
│   ├── embedders/              # Text embedding generation
│   └── extractors/             # Document format extractors
├── Module3_NiruDB/             # Database management
│   ├── populate_db.py          # Database initialization
│   ├── metadata_manager.py     # Metadata operations
│   └── vector_store.py         # Vector database interface
├── Module4_NiruAPI/            # REST API and web services
│   ├── api.py                  # FastAPI application
│   ├── rag_pipeline.py         # RAG implementation
│   ├── sms_pipeline.py         # SMS processing
│   └── models/                 # Pydantic models
├── Module5_NiruShare/          # Social media sharing
│   ├── api.py                  # Sharing endpoints
│   ├── service.py              # Sharing logic
│   └── formatters/             # Platform-specific formatters
├── frontend/                   # React/Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js app router
│   │   ├── components/         # Reusable components
│   │   └── lib/                # Utilities
│   └── public/                 # Static assets
├── config/                     # Configuration files
├── docs/                       # Documentation
├── examples/                   # Usage examples
└── tests/                      # Test suites
```

## Contributing Guidelines

### Types of Contributions

- **🐛 Bug Fixes**: Fix bugs and issues
- **✨ Features**: Add new features
- **📚 Documentation**: Improve documentation
- **🎨 UI/UX**: Enhance user interface and experience
- **🔧 Maintenance**: Code refactoring and maintenance
- **🧪 Testing**: Add or improve tests

### Development Workflow

1. **Choose an Issue**: Look for open issues or create a new one
2. **Create a Branch**: Use descriptive branch names
   ```bash
   git checkout -b feature/add-new-spider
   git checkout -b bugfix/fix-parsing-error
   git checkout -b docs/update-contributing-guide
   ```

3. **Make Changes**: Follow the code style guidelines
4. **Test Your Changes**: Ensure tests pass and functionality works
5. **Commit Changes**: Write clear, descriptive commit messages
   ```bash
   git commit -m "feat: add support for PDF document parsing

   - Add PDF extraction using PyPDF2
   - Handle encrypted PDFs gracefully
   - Add tests for PDF processing
   - Update documentation"
   ```

6. **Push and Create PR**: Push your branch and create a pull request

### Commit Message Format

We follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

## Code Style

### Python

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use docstrings for all public functions and classes
- Maximum line length: 88 characters (Black formatter default)

### JavaScript/TypeScript

- Use ESLint and Prettier for code formatting
- Use TypeScript for type safety
- Follow React best practices
- Use functional components with hooks

### Code Quality Tools

```bash
# Python
pip install black isort flake8 mypy
black .                    # Format code
isort .                    # Sort imports
flake8 .                   # Lint code
mypy .                     # Type checking

# JavaScript/TypeScript
npm run lint              # ESLint
npm run format            # Prettier
```

## Testing

### Running Tests

```bash
# Python tests
pytest

# Frontend tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

### Writing Tests

- Write unit tests for all new functions
- Include integration tests for API endpoints
- Add end-to-end tests for critical user flows
- Maintain test coverage above 80%

### Test Structure

```
tests/
├── unit/                  # Unit tests
├── integration/          # Integration tests
├── e2e/                  # End-to-end tests
└── fixtures/             # Test data
```

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass** and code is properly formatted
2. **Update documentation** if needed
3. **Add migration scripts** for database changes
4. **Test deployment** in a staging environment
5. **Create a pull request** with a clear description

### PR Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots of UI changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Migration scripts added (if applicable)
```

## Community

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and community discussion
- **Pull Requests**: For code contributions

### Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Report any unacceptable behavior

### Recognition

Contributors will be recognized in:
- GitHub repository contributors list
- CHANGELOG.md for significant contributions
- Project documentation

## License

By contributing to AmaniQuery, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AmaniQuery! Your efforts help democratize access to legal information in Kenya. 🚀
