# FinSight Development Guide

## Overview

This guide provides comprehensive information for developers working on the FinSight project, including setup instructions, coding standards, and development workflows.

## Development Environment Setup

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- Docker (optional)
- AWS CLI (for deployment)
- Git

### Initial Setup

1. **Clone Repository**

```bash
git clone https://github.com/your-username/FinSight.git
cd FinSight
```

2. **Python Environment**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Frontend Setup**

```bash
cd frontend
npm install
```

4. **Environment Configuration**

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your configuration
nano .env
```

## Project Structure

```
FinSight/
├── src/
│   ├── handlers/
│   ├── models/
│   ├── integrations/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── deployment/
│   ├── aws/
│   └── docker/
└── docs/
```

## Development Workflow

### 1. Branch Management

```bash
# Create feature branch
git checkout -b feature/new-feature

# Create bugfix branch
git checkout -b fix/bug-description

# Create release branch
git checkout -b release/v1.0.0
```

### 2. Code Style

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/TypeScript
- Use Black for Python formatting
- Use isort for import sorting

```bash
# Format Python code
black src/
isort src/

# Format frontend code
cd frontend
npm run lint
npm run format
```

### 3. Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run all tests with coverage
pytest --cov=src tests/
```

### 4. Local Development

```bash
# Start backend server
python api_server.py

# Start frontend development server
cd frontend
npm run dev
```

## API Development

### 1. Adding New Endpoints

```python
from fastapi import APIRouter, HTTPException
from src.models.enrichment_models import EnrichmentRequest

router = APIRouter()

@router.post("/new-endpoint")
async def new_endpoint(request: EnrichmentRequest):
    try:
        # Implementation
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Data Models

```python
from pydantic import BaseModel
from typing import List, Optional

class NewModel(BaseModel):
    field1: str
    field2: int
    field3: Optional[List[str]] = None
```

### 3. Error Handling

```python
from src.utils.exceptions import FinSightError

class CustomError(FinSightError):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
```

## Frontend Development

### 1. Component Structure

```typescript
// src/components/NewComponent.tsx
import React from 'react';

interface Props {
  data: string;
  onAction: () => void;
}

export const NewComponent: React.FC<Props> = ({ data, onAction }) => {
  return (
    <div>
      {/* Component implementation */}
    </div>
  );
};
```

### 2. API Integration

```typescript
// src/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchData = async () => {
  const response = await api.get('/endpoint');
  return response.data;
};
```

## Database Development

### 1. Schema Changes

```python
# src/models/database.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewTable(Base):
    __tablename__ = 'new_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    created_at = Column(DateTime)
```

### 2. Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
```

## Performance Optimization

### 1. Caching

```python
from src.utils.cache import Cache

cache = Cache()

@cache.memoize(ttl=3600)
async def expensive_operation():
    # Implementation
    pass
```

### 2. Async Operations

```python
import asyncio
from src.utils.async_utils import gather_with_concurrency

async def process_items(items):
    async def process_item(item):
        # Process single item
        pass
    
    return await gather_with_concurrency(10, [process_item(item) for item in items])
```

## Security Best Practices

### 1. API Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

### 2. Data Validation

```python
from pydantic import BaseModel, validator

class SecureModel(BaseModel):
    data: str
    
    @validator('data')
    def validate_data(cls, v):
        if not v.isalnum():
            raise ValueError('Data must be alphanumeric')
        return v
```

## Deployment

### 1. AWS Deployment

```bash
# Deploy to development
cd deployment/aws
./deploy.sh --stage dev

# Deploy to production
./deploy.sh --stage prod
```

### 2. Docker Deployment

```bash
# Build image
docker build -t finsight .

# Run container
docker run -p 8000:8000 finsight
```

## Monitoring and Logging

### 1. Logging Configuration

```python
import logging
from src.utils.logging import setup_logging

logger = setup_logging(__name__)

def some_function():
    logger.info("Processing request")
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise
```

### 2. Metrics Collection

```python
from src.utils.metrics import Metrics

metrics = Metrics()

@metrics.track_time
async def measured_function():
    # Implementation
    pass
```

## Troubleshooting

### Common Issues

1. **Database Connection**
   - Check connection string
   - Verify database is running
   - Check network connectivity

2. **API Issues**
   - Check API keys
   - Verify endpoint URLs
   - Check request/response format

3. **Performance Issues**
   - Check cache configuration
   - Monitor resource usage
   - Review query performance

## Contributing

1. **Code Review Process**
   - Create pull request
   - Address review comments
   - Update documentation
   - Run all tests

2. **Documentation**
   - Update API documentation
   - Add code comments
   - Update README if needed
   - Document breaking changes

3. **Release Process**
   - Update version numbers
   - Update changelog
   - Create release branch
   - Deploy to staging 