# .test Directory

This directory contains all project tests, mirroring the main codebase structure.

## Structure

```
.test/
├── backend/                # Backend tests
│   ├── test_financial_handlers.py
│   ├── test_operational_handlers.py
│   └── ...
├── frontend/               # Frontend tests (if applicable)
└── test_*.py               # Root-level integration tests
```

## Naming Convention

All test files must follow the pattern: `test_*.py`

## Running Tests

```bash
# Run all tests
pytest .test/ -v

# Run with coverage
pytest .test/ --cov=backend --cov-report=html

# Run specific test file
pytest .test/backend/test_financial_handlers.py -v

# Run tests matching pattern
pytest .test/ -k "test_take_loan"
```

## Test Logging

Test logs are written to `.log/tests/pytest.log` as configured in `pytest.ini`.

## Writing Tests

1. Mirror the source file path in `.test/`
2. Use `pytest` fixtures for setup/teardown
3. Follow AAA pattern: Arrange, Act, Assert
4. Use descriptive test names: `test_take_loan_increases_debt`

## Example

```python
# .test/backend/test_financial_handlers.py

import pytest
from backend.command_handlers.financial_handlers import TakeLoanHandler
from backend.core.models import AgentState

def test_take_loan_increases_debt():
    # Arrange
    state = AgentState(agent_id="TEST", cash_balance=1000.0)
    handler = TakeLoanHandler()
    
    # Act
    events = handler.handle(state, Command(...))
    
    # Assert
    assert len(events) == 1
    assert events[0].event_type == "LoanTaken"
```
