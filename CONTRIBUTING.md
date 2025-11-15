# Contributing to Family Photo Hub

Thank you for your interest in contributing to Family Photo Hub!

## Development Setup

See the main [README.md](README.md) for detailed setup instructions.

Quick start:
```bash
bash scripts/setup.sh
```

## Project Structure

- `backend/` - FastAPI backend application
- `frontend/` - Next.js frontend application
- `scripts/` - Development and deployment scripts
- `.cursor/rules/` - AI assistant rules and conventions

## Code Style

### Backend (Python)
- Follow PEP8
- Use Black for formatting (max line length: 100)
- Use isort for import ordering
- Type hints are mandatory
- Run consistency checks: `python scripts/consistency_check.py`

### Frontend (TypeScript)
- Use Prettier and ESLint
- Strong typing mandatory (no `any` unless justified)
- No business logic in components

## Before Submitting

1. Run tests: `make test`
2. Run linters: `make lint`
3. Format code: `make format`
4. Ensure all checks pass in CI

## Naming Conventions

### Python/Backend
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- DB tables: singular (`media`, `user`)

### TypeScript/Frontend
- Components: `PascalCase.tsx`
- Hooks: `useSomething.ts`
- Utilities: `camelCase.ts`

## Commit Messages

Use conventional commits format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks

Example: `feat: add face clustering to AI service`

## Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes
3. Ensure all tests pass
4. Submit PR to `develop` branch
5. Wait for review

## Questions?

Refer to the [README.md](README.md) or project documentation.
