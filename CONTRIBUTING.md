# Contributing to FinSight

## Overview

Thank you for your interest in contributing to FinSight! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- Git
- Docker (optional)
- AWS CLI (for deployment)

### Development Environment Setup

1. **Fork the Repository**

```bash
# Fork on GitHub
# Clone your fork
git clone https://github.com/your-username/FinSight.git
cd FinSight

# Add upstream remote
git remote add upstream https://github.com/original-owner/FinSight.git
```

2. **Setup Python Environment**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Setup Frontend**

```bash
cd frontend
npm install
```

## Development Workflow

### 1. Branch Management

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/your-bug-description

# Create documentation branch
git checkout -b docs/your-doc-update
```

### 2. Making Changes

1. **Code Style**
   - Follow PEP 8 for Python code
   - Use ESLint for JavaScript/TypeScript
   - Use Black for Python formatting
   - Use isort for import sorting

2. **Testing**
   - Write unit tests for new features
   - Update existing tests if needed
   - Ensure all tests pass

3. **Documentation**
   - Update relevant documentation
   - Add docstrings to new functions
   - Update API documentation

### 3. Committing Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/your-feature-name
```

### 4. Pull Request Process

1. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Describe changes clearly

2. **PR Review**
   - Address review comments
   - Update PR if needed
   - Ensure CI passes

3. **Merge**
   - Squash commits if needed
   - Update documentation
   - Delete branch after merge

## Coding Standards

### Python

```python
# Use type hints
def process_data(data: List[str]) -> Dict[str, Any]:
    """Process the input data.
    
    Args:
        data: List of strings to process
        
    Returns:
        Dictionary containing processed data
    """
    pass

# Use dataclasses for data models
@dataclass
class User:
    id: int
    name: str
    email: str
```

### JavaScript/TypeScript

```typescript
// Use interfaces for types
interface User {
  id: number;
  name: string;
  email: string;
}

// Use async/await
async function fetchData(): Promise<User> {
  const response = await api.get('/user');
  return response.data;
}
```

## Testing

### Unit Tests

```python
# tests/unit/test_feature.py
import pytest
from src.feature import process_data

def test_process_data():
    input_data = ["test"]
    result = process_data(input_data)
    assert result is not None
    assert len(result) > 0
```

### Integration Tests

```python
# tests/integration/test_api.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_api_endpoint():
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## Documentation

### Code Documentation

```python
def complex_function(param1: str, param2: int) -> bool:
    """Perform a complex operation.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        True if operation successful, False otherwise
        
    Raises:
        ValueError: If parameters are invalid
    """
    pass
```

### API Documentation

```python
@router.post("/api/endpoint")
async def api_endpoint(
    request: RequestModel = Body(..., example={"key": "value"})
) -> ResponseModel:
    """Process API request.
    
    Args:
        request: Request model containing input data
        
    Returns:
        Response model containing processed data
        
    Raises:
        HTTPException: If request is invalid
    """
    pass
```

## Review Process

### Code Review Checklist

1. **Functionality**
   - Does it work as expected?
   - Are edge cases handled?
   - Is error handling appropriate?

2. **Code Quality**
   - Is the code readable?
   - Are there any code smells?
   - Is the code maintainable?

3. **Testing**
   - Are tests comprehensive?
   - Do tests cover edge cases?
   - Are tests maintainable?

4. **Documentation**
   - Is documentation clear?
   - Are examples provided?
   - Is API documented?

## Release Process

### Version Bumping

```bash
# Update version in setup.py
version = "1.0.0"

# Update version in package.json
{
  "version": "1.0.0"
}
```

### Changelog Updates

```markdown
## [1.0.0] - 2024-03-20

### Added
- New feature
- Documentation updates

### Changed
- Improved performance
- Updated dependencies

### Fixed
- Bug fixes
- Security updates
```

## Communication

### Issue Reporting

1. **Bug Reports**
   - Use the bug report template
   - Include steps to reproduce
   - Provide error messages
   - Include environment details

2. **Feature Requests**
   - Use the feature request template
   - Describe the feature
   - Explain use cases
   - Suggest implementation

### Discussion

- Use GitHub Discussions
- Join our Slack channel
- Participate in community calls

## License

By contributing to FinSight, you agree that your contributions will be licensed under the project's MIT License.

## Acknowledgments

- Thanks to all contributors
- Inspired by the community
- Built with modern tools
- Deployed on AWS
