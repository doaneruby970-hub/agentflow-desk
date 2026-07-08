# Contributing to AgentFlow Desk

Thank you for your interest in contributing to AgentFlow Desk!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agentflow-desk.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest tests/ -v`
6. Run linting: `ruff check app/ tests/`
7. Commit your changes: `git commit -m "Add feature X"`
8. Push to your fork: `git push origin feature/your-feature-name`
9. Create a Pull Request

## Development Setup

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start infrastructure
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Write docstrings for public functions and classes
- Maximum line length: 100 characters
- Use `ruff` for formatting and linting

## Testing

- Write tests for all new features
- Maintain test coverage > 80%
- Run tests before submitting PR: `pytest tests/ -v --cov=app`

## Pull Request Guidelines

- Keep PRs focused on a single feature or bug fix
- Update documentation for user-facing changes
- Add tests for new functionality
- Ensure all CI checks pass
- Write clear commit messages

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Provide error messages and logs
- Specify your environment (OS, Python version, etc.)

## Questions?

Open an issue with the "question" label.
