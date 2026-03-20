# Contributing to Canopy

Thank you for your interest in contributing to Canopy. This document outlines the development workflow and standards for contributions.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- Docker (optional, for full stack testing)

### Local Environment

```bash
# Clone repository
git clone https://github.com/griffinmacnaughtan/canopy.git
cd canopy

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Running Tests

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm test
```

## Code Standards

### Python (Backend)

- **Formatter**: Use `black` with default settings
- **Linter**: Use `ruff` for fast linting
- **Type hints**: Required for all function signatures
- **Docstrings**: Google style for public functions

```python
def calculate_risk(
    assets: List[Asset],
    scenario: str,
) -> RiskScore:
    """Calculate portfolio risk under a given scenario.

    Args:
        assets: List of portfolio assets with emissions data.
        scenario: NGFS scenario name (e.g., "Net Zero 2050").

    Returns:
        RiskScore containing transition, physical, and overall metrics.

    Raises:
        ValueError: If scenario name is not recognized.
    """
    ...
```

### TypeScript (Frontend)

- **Formatter**: Prettier with project config
- **Linter**: ESLint with strict TypeScript rules
- **Types**: No `any` types; use proper interfaces

```typescript
interface ScoreCardProps {
  title: string;
  value: number;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
}

export function ScoreCard({ title, value, trend, description }: ScoreCardProps) {
  // ...
}
```

### Commit Messages

Use conventional commits:

```
feat: add TCFD compliance indicator to dashboard
fix: correct emissions intensity calculation for zero-revenue assets
docs: update API reference for scenario endpoint
test: add integration tests for portfolio creation
refactor: extract scoring logic into separate module
```

Prefix types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code restructuring without behavior change
- `chore`: Maintenance tasks

## Pull Request Process

1. **Branch naming**: `feat/description`, `fix/description`, `docs/description`

2. **PR description template**:
   ```markdown
   ## Summary
   Brief description of changes.

   ## Changes
   - Bullet points of specific changes

   ## Testing
   - How you tested these changes

   ## Screenshots
   If UI changes, include before/after.
   ```

3. **Review checklist**:
   - [ ] Tests pass locally
   - [ ] No type errors
   - [ ] Lint passes
   - [ ] Documentation updated if needed
   - [ ] No sensitive data in commits

4. **Merge**: Squash and merge to keep history clean

## Architecture Guidelines

### Adding New API Endpoints

1. Create route module in `backend/app/routes/`
2. Add Pydantic request/response models in `backend/app/models.py`
3. Register router in `backend/app/routes/__init__.py`
4. Add integration tests in `backend/tests/integration/`
5. Update API client in `frontend/src/api/client.ts`
6. Add mock data if supporting demo mode

### Adding New Pipeline Sources

1. Create extractor in `backend/app/pipeline/extractors/`
2. Inherit from `BaseExtractor` and implement `extract()` and `health_check()`
3. Add transformer in `backend/app/pipeline/transformers/`
4. Update schema validator if new data shape
5. Register in main flow in `backend/app/pipeline/flows.py`
6. Add unit tests

### Frontend Components

- Place reusable UI primitives in `components/ui/`
- Place feature components in `components/{feature}/`
- Use TanStack Query for server state
- Use React Context only for truly global state (portfolio selection)
- Export from barrel files (`index.ts`)

## Questions

Open an issue for:
- Feature requests
- Bug reports
- Architecture discussions

For security issues, email directly (do not open public issues).
