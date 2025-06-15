# Agent Simulation Tests

This directory contains comprehensive tests for FinSight's AI agent simulation capabilities, including advanced scenarios and multi-agent interactions.

## Files

- **`test_agent_simulation.py`** - Core agent simulation tests
- **`test_advanced_agent_scenarios.py`** - Advanced multi-agent scenarios and edge cases

## Test Coverage

### Basic Agent Simulation (`test_agent_simulation.py`)
- Single agent financial analysis
- Data retrieval and processing
- Response formatting and validation
- Error handling scenarios

### Advanced Scenarios (`test_advanced_agent_scenarios.py`)
- Multi-agent collaboration
- Complex financial analysis workflows
- Edge case handling
- Performance under load
- Integration with external APIs

## Running Tests

```bash
# Run all agent simulation tests
python -m pytest tests/agent_simulation/ -v

# Run specific test file
python tests/agent_simulation/test_agent_simulation.py
python tests/agent_simulation/test_advanced_agent_scenarios.py

# Run with coverage
python -m pytest tests/agent_simulation/ --cov=src --cov-report=html
```

## Test Requirements

- FinSight API server running on localhost:8000
- Valid AWS credentials (for Bedrock integration)
- Internet connection (for external API tests)
- Test data fixtures (automatically generated)

## Configuration

Tests use the same configuration as the main application:
- Environment variables from `.env.local`
- AWS region and credentials
- API endpoints and timeouts

## Continuous Integration

These tests are part of the CI/CD pipeline and run automatically on:
- Pull requests
- Main branch commits
- Scheduled nightly runs

## Debugging

For debugging failed tests:
```bash
# Run with verbose output
python tests/agent_simulation/test_agent_simulation.py -v

# Run specific test method
python -m pytest tests/agent_simulation/test_agent_simulation.py::TestClass::test_method -v -s
``` 