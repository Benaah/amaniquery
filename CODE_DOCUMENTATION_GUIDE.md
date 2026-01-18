# Code Documentation Guidelines for AmaniQuery

> Standards for documenting code, APIs, and modules across the AmaniQuery codebase.

**Based on:** `.agent/skills/documentation-templates/SKILL.md`

---

## 📋 Overview

This guide ensures consistent, AI-friendly documentation across AmaniQuery's 9 modules and shared code. Follow these standards when writing docstrings, comments, and markdown documentation.

---

## 🎯 Core Principles

### 1. **Self-Documenting Code First**
- Write clear, descriptive variable/function names
- Use type hints in all Python code
- Structure code logically
- Comments explain **why**, not **what**

### 2. **Documentation Templates**
All module-level documentation should follow standard templates:

| Document Type | Template | Location |
|---------------|----------|----------|
| Module README | [Module Template](#module-readme-template) | `ModuleX_Name/README.md` |
| API Endpoint | [API Template](#api-endpoint-template) | Inline docstrings + docs |
| Function | [Function Template](#function-docstring-template) | Code docstrings |
| Class | [Class Template](#class-docstring-template) | Code docstrings |

### 3. **Progressive Detail**
- **Level 1**: One-line summary (what it does)
- **Level 2**: Key features and usage examples
- **Level 3**: Detailed parameters, returns, and implementation notes

### 4. **AI-Friendly Format**
- Clear H1-H3 hierarchy
- Code blocks with language tags
- Tables for parameters/config
- Examples before explanations
- Mermaid diagrams for complex flows

---

## 📖 Module README Template

```markdown
# Module X: ModuleName

![Module](path/to/image.png)

One-line description of what this module does.

## 🏗️ Structure

```
ModuleX_Name/
├── component1/          # Brief description
├── component2/          # Brief description
└── main.py             # Entry point
```

## ✨ Features

- Feature 1: Brief explanation
- Feature 2: Brief explanation
- Feature 3: Brief explanation

## 🚀 Usage

### Quick Start
```python
from ModuleX_Name import main_function

result = main_function(input)
```

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| param1 | str | None | Required: Explanation |
| param2 | int | 100 | Optional: Explanation |

## 📤 Output

What this module produces:
- File formats
- Locations
- Metadata structure

## 🔗 Dependencies

- External services
- Database connections
- API keys required

---

<div align="center">

[← Back to Main README](../README.md) | [View All Modules](../docs/DOCUMENTATION_INDEX.md)

</div>
```

---

## 📝 Function Docstring Template

### Python Functions

```python
def function_name(param1: type, param2: type = default) -> return_type:
    """
    Brief one-line description of what the function does.
    
    More detailed explanation if needed. Include context, 
    business logic explanation, and important notes.
    
    Args:
        param1 (type): Description of parameter
        param2 (type): Description of parameter
        
    Returns:
        return_type: Description of what is returned
        
    Raises:
        ValueError: When this specific error occurs
        ConnectionError: When this specific error occurs
        
    Examples:
        >>> # Basic usage
        >>> result = function_name("input", 42)
        >>> print(result)
        expected_output
        
        >>> # With specific parameters
        >>> result = function_name("special", 100)
        >>> print(result)
        special_output
        
    Notes:
        - Important implementation detail
        - Performance consideration
        - Known limitation
    """
```

### When to Use Detailed Docstrings
✅ **DO** use for:
- Public API functions
- Complex algorithms
- Business-critical logic
- Functions with side effects
- Functions with complex parameters

❌ **DON'T** need for:
- Private/helper functions (use simple comments)
- Obvious getters/setters
- One-line lambdas
- Standard library wrappers

---

## 🏗️ Class Docstring Template

```python
class ClassName:
    """
    Brief one-line description of the class.
    
    Detailed explanation of the class purpose, use cases,
    and relationship to other components.
    
    Attributes:
        attr1 (type): Description of attribute
        attr2 (type): Description of attribute
        
    Examples:
        >>> # Basic instantiation
        >>> obj = ClassName(param1="value")
        >>> obj.method()
        expected_result
        
    See Also:
        RelatedClass: Brief explanation of relationship
        OtherClass: Brief explanation of relationship
    """
    
    def __init__(self, param1: type, param2: type):
        """
        Initialize ClassName with parameters.
        
        Args:
            param1: Description
            param2: Description
        """
```

---

## 🎯 API Endpoint Documentation

### REST API Template

```python
@app.get("/endpoint/{param}")
async def endpoint_name(param: str, query: Optional[str] = None):
    """
    Brief endpoint description.
    
    Detailed description of what this endpoint does,
    use cases, and important notes.
    
    ## Parameters
    
    **Path Parameters:**
    | Parameter | Type | Required | Description |
    |-----------|------|----------|-------------|
    | param | string | Yes | Description |
    
    **Query Parameters:**
    | Parameter | Type | Required | Default | Description |
    |-----------|------|----------|---------|-------------|
    | query | string | No | None | Description |
    
    ## Responses
    
    ### 200 OK
    Successful response description.
    
    ```json
    {
        "field1": "value1",
        "field2": "value2"
    }
    ```
    
    ### 404 Not Found
    Resource not found.
    
    ```json
    {
        "error": "Resource not found",
        "detail": "Additional information"
    }
    ```
    
    ## Examples
    
    ```bash
    # Example request
curl -X GET "https://api.amaniquery.com/endpoint/value?query=test"
    ```
    
    ## Authentication
    
    Requires `Authorization: Bearer <token>` header.
    
    ## Rate Limit
    
    100 requests per minute per user.
    """
```

---

## 💬 Code Comment Guidelines

### ✅ **DO Comment:**
- **Why** not **What**: Explain business logic, not obvious code
- **Complex algorithms**: High-level approach before implementation
- **Non-obvious behavior**: Edge cases, assumptions, gotchas
- **API contracts**: What calling code should expect
- **Performance notes**: Time/space complexity, optimization rationale
- **TODOs/FIXMEs**: With ticket numbers or dates

### ❌ **DON'T Comment:**
```python
# ❌ BAD
# Increment counter by 1
counter += 1

# ❌ BAD  
# This is a function that adds two numbers
def add(a, b):
    return a + b

# ✅ GOOD
def add_user_to_database(user_data: dict) -> int:
    """
    Add new user and return user_id.
    
    Duplicates are prevented by unique email constraint.
    Sends welcome email asynchronously.
    """
```

### Comment Types

```python
# TODO: Add retry logic for transient failures (issue #123)
# FIXME: This breaks for edge case X, needs refactor by Q2
# NOTE: This approach chosen for performance reasons (40% faster than alternative)
# WARNING: Changing this constant breaks backward compatibility
# REVIEW: Should we validate this input more strictly?

# HINT FOR AI AGENTS:
# - When modifying this function, check Unit tests at tests/test_user_service.py
# - Update API docs at docs/API_REFERENCE.md
# - Run integration tests: pytest tests/integration/test_user_flow.py
```

---

## 📊 Documentation Coverage Requirements

### Module-Level
✅ README.md with structure, features, usage
✅ API documentation (if applicable)
✅ Configuration examples
✅ Output format specifications

### Code-Level
✅ Public functions/classes: Full docstrings
✅ Complex private functions: Inline comments
✅ API endpoints: Full parameter/response docs
✅ Database schemas: Field descriptions

### Integration-Level
✅ Inter-module dependencies documented
✅ Environment variables listed in `.env.example`
✅ Setup/deployment scripts documented
✅ Error handling and recovery documented

---

## 🔄 Documentation Maintenance

### When to Update Documentation

| Change Type | Documentation to Update |
|-------------|------------------------|
| **New feature** | Module README, API docs, main README features |
| **API change** | Docstrings, API reference, migration guide |
| **New module** | Full module README, architecture docs, main README structure |
| **Dependency update** | Setup guides, requirements, compatibility notes |
| **Bug fix** | Comments explaining the fix, changelog |
| **Performance change** | Comments with benchmarks, optimization rationale |

### Documentation Checklist

Before merging changes:

- [ ] Code has appropriate docstrings
- [ ] Complex logic has explanatory comments
- [ ] Module README updated (if applicable)
- [ ] API documentation updated (if applicable)
- [ ] Examples are correct and tested
- [ ] Cross-references to related docs added
- [ ] No broken links in documentation
- [ ] Spelling and grammar checked

---

## 🎯 Special Cases

### FastAPI/SQLAlchemy Models

```python
class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)  # Unique identifier
    email = Column(String, unique=True, index=True)  # Login email, indexed for fast lookup
    created_at = Column(DateTime, default=datetime.utcnow)  # Account creation timestamp
    
    # Relationships
    queries = relationship("Query", back_populates="user")  # User's query history
```

### Configuration Files

```python
# config.py
"""
Configuration management for AmaniQuery.

This module loads and validates configuration from:
- Environment variables
- config.yaml file
- Default values

Sensitive values (API keys, passwords) should NEVER be in this file.
Use environment variables or .env file instead.
"""

# Database configuration
# Use vector store optimized for semantic search
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectors")
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "384"))
```

### Error Handling

```python
try:
    result = risky_operation()
except RateLimitError as e:
    # Back off and retry with exponential delay
    # See: https://platform.openai.com/docs/guides/rate-limits
    retry_after = int(e.headers.get("Retry-After", 60))
    time.sleep(retry_after)
    raise  # Re-raise to trigger retry logic in caller
```

---

## 📖 Examples of Good Documentation

### Before (Poor)
```python
def calc(user, data):
    # Process user data
    x = 0
    for i in data:
        if i.type == "special":
            x += i.value * 2
        else:
            x += i.value
    return x
```

### After (Good)
```python
def calculate_user_credit_score(user_id: int, transactions: List[Transaction]) -> int:
    """
    Calculate credit score based on transaction history.
    
    Special transactions (loans, mortgages) are weighted double
    compared to regular transactions (purchases, payments).
    
    Args:
        user_id: User identifier
        transactions: List of user's financial transactions
        
    Returns:
        Integer credit score from 300-850
        
    Raises:
        ValueError: If user_id is invalid or transactions empty
        
    Examples:
        >>> transactions = [
        ...     Transaction(type="purchase", value=500),
        ...     Transaction(type="loan", value=1000)  # Weighted double
        ... ]
        >>> score = calculate_user_credit_score(123, transactions)
        >>> print(score)  # (500 + 1000*2) = 2500
        2500
    """
    if not user_id or not transactions:
        raise ValueError("Invalid user_id or empty transactions")
    
    total_score = 0
    for transaction in transactions:
        # Special transactions have higher impact on credit score
        weight = 2.0 if transaction.type in SPECIAL_TRANSACTIONS else 1.0
        total_score += transaction.value * weight
    
    return min(max(int(total_score), 300), 850)  # Clamp to valid range
```

---

## 🏁 Summary

**Remember:**
1. Write self-documenting code with clear names and types
2. Explain **why**, not **what**
3. Provide examples for public APIs
4. Keep comments current with code
5. Update module READMEs when features change
6. Follow templates for consistency
7. Think about the next developer (or AI agent) reading your code

**References:**
- [Documentation Templates Skill](../.agent/skills/documentation-templates/SKILL.md)
- [Documentation Index](../docs/DOCUMENTATION_INDEX.md)
- [Contributing Guide](./CONTRIBUTING.md)

---

<div align="center">

**Next Step:** Apply these guidelines when contributing to AmaniQuery

[← Back to README](./README.md) | [View All Docs →](./docs/DOCUMENTATION_INDEX.md)

</div>
