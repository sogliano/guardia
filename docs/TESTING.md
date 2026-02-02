# Testing Guide

Estrategia de testing, convenciones, y guías para escribir tests en Guard-IA. Cubre backend (pytest), frontend (Vitest + Playwright), y CI/CD.

---

## Testing Strategy

### Coverage Targets

| Componente | Target | Tool | Comando |
|-----------|--------|------|---------|
| Backend | **≥60%** | pytest-cov | `pytest --cov=app --cov-report=term-missing` |
| Frontend | **≥30%** | vitest | `npm run test:coverage` |
| E2E | Critical flows | Playwright | `npm run test:e2e` |

### Test Pyramid

Seguimos la pirámide de testing estándar:

```
        /\
       /E2E\      10% - End-to-End (Playwright)
      /------\    User flows críticos
     /  INT  \    20% - Integration
    /----------\  API endpoints, DB, external services
   /   UNIT    \  70% - Unit tests
  /--------------\ Logic, services, stores, components
```

**Razón:**
- Unit tests: rápidos (<1s), aislados, fáciles de debuggear
- Integration: más lentos (~2-5s), verifican interacciones reales
- E2E: lentos (10-30s), costosos de mantener, pero validan UX completa

### Test Types

#### Unit Tests (70%)
- Business logic pura
- Services (sin DB, con mocks)
- Stores (Pinia)
- Composables (Vue)
- Heuristics
- Utilities

#### Integration Tests (20%)
- API endpoints (con DB real en test)
- Database queries (SQLAlchemy)
- External services (OpenAI, Clerk - con mocks)
- Pipeline completo (con mocks de LLM)

#### E2E Tests (10%)
- Login flow
- Dashboard navigation
- Case resolution
- Email quarantine release
- Filters + search

---

## Backend Testing (pytest)

### Structure

```
tests/
├── unit/                     # Fast, isolated
│   ├── test_heuristics.py
│   ├── test_utils.py
│   └── services/
│       ├── test_case_service.py
│       └── test_email_service.py
├── integration/              # DB, external services
│   ├── test_api_cases.py
│   ├── test_api_emails.py
│   ├── test_pipeline.py
│   └── test_auth.py
└── conftest.py               # Fixtures compartidos
```

### Setup

**Install test dependencies:**
```bash
cd backend
pip install pytest pytest-asyncio pytest-cov httpx
```

**Configure pytest:**
```ini
# backend/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
```

### Writing Unit Tests

#### Example: Testing Service (with mocks)

```python
# tests/unit/services/test_case_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.services.case_service import CaseService
from app.models.case import Case

@pytest.mark.asyncio
async def test_list_cases():
    """Test list_cases with pagination."""
    # Arrange
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Case(id=uuid4(), status="pending"),
        Case(id=uuid4(), status="analyzing"),
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Mock count query
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2
    mock_db.execute.side_effect = [mock_count_result, mock_result]

    svc = CaseService(mock_db)

    # Act
    result = await svc.list_cases(page=1, size=20)

    # Assert
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["page"] == 1
    assert result["size"] == 20

@pytest.mark.asyncio
async def test_get_case_not_found():
    """Test get_case raises NotFoundError."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = CaseService(mock_db)

    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await svc.get_case(uuid4())
```

#### Example: Testing Heuristics

```python
# tests/unit/test_heuristics.py
import pytest
from app.services.pipeline.heuristics import HeuristicsEngine
from app.models.email import Email

def test_check_suspicious_sender():
    """Test suspicious sender detection."""
    engine = HeuristicsEngine()

    # Suspicious: domain mismatch
    email = Email(
        sender="ceo@evil.com",
        display_name="CEO Strike Security",
        body="Urgent payment required",
    )
    result = engine.check_suspicious_sender(email)
    assert result.score > 0.5
    assert "domain mismatch" in result.reason.lower()

    # Legitimate
    email = Email(
        sender="john@strike.sh",
        display_name="John Doe",
        body="Meeting tomorrow",
    )
    result = engine.check_suspicious_sender(email)
    assert result.score == 0.0

def test_check_urgency_keywords():
    """Test urgency detection."""
    engine = HeuristicsEngine()

    urgent_phrases = [
        "URGENT: Your account will be suspended",
        "Act now or lose access",
        "Immediate action required",
        "Verify your account within 24 hours",
    ]

    for phrase in urgent_phrases:
        email = Email(subject=phrase, body=phrase)
        result = engine.check_urgency(email)
        assert result.score > 0.3, f"Failed for: {phrase}"

@pytest.mark.parametrize("url,expected_score", [
    ("https://google.com", 0.0),  # Legitimate
    ("http://g00gle.com", 0.7),  # Typosquatting
    ("https://strike-security.evil.com", 0.6),  # Subdomain spoofing
    ("https://bit.ly/xxx", 0.4),  # Shortened URL
])
def test_check_suspicious_urls(url, expected_score):
    """Test URL analysis."""
    engine = HeuristicsEngine()
    email = Email(body=f"Click here: {url}")
    result = engine.check_suspicious_urls(email)
    assert abs(result.score - expected_score) < 0.2
```

### Writing Integration Tests

#### Example: Testing API Endpoints (with DB)

```python
# tests/integration/test_api_cases.py
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.case import Case
from app.models.email import Email

@pytest.mark.asyncio
async def test_list_cases_endpoint(client: AsyncClient, db_session, auth_headers):
    """Test GET /cases endpoint."""
    # Arrange: create test data
    case1 = Case(status="pending", final_score=0.5)
    case2 = Case(status="resolved", final_score=0.2)
    db_session.add_all([case1, case2])
    await db_session.commit()

    # Act
    response = await client.get("/api/v1/cases", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert "items" in data
    assert all("id" in item for item in data["items"])

@pytest.mark.asyncio
async def test_resolve_case_endpoint(client: AsyncClient, db_session, auth_headers):
    """Test POST /cases/{id}/resolve endpoint."""
    # Arrange
    case = Case(status="pending", final_score=0.7)
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    # Act
    response = await client.post(
        f"/api/v1/cases/{case.id}/resolve",
        json={"verdict": "allowed"},
        headers=auth_headers,
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert data["final_verdict"] == "allowed"

@pytest.mark.asyncio
async def test_rate_limit_cases_endpoint(client: AsyncClient, auth_headers):
    """Test rate limiting on /cases endpoint."""
    # Act: make 61 requests (limit is 60/minute)
    responses = []
    for _ in range(61):
        resp = await client.get("/api/v1/cases", headers=auth_headers)
        responses.append(resp)

    # Assert
    assert responses[-1].status_code == 429  # Last request should be rate limited
    assert "X-RateLimit-Remaining" in responses[0].headers
```

#### Example: Testing Pipeline (with mocks)

```python
# tests/integration/test_pipeline.py
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from app.services.pipeline.orchestrator import PipelineOrchestrator
from app.models.email import Email
from app.models.case import Case

@pytest.mark.asyncio
async def test_pipeline_full_flow(db_session):
    """Test complete pipeline execution."""
    # Arrange
    email = Email(
        sender="phishing@evil.com",
        recipient="user@strike.sh",
        subject="URGENT: Verify your account",
        body="Click here to verify: http://evil.com/verify",
    )
    db_session.add(email)
    await db_session.commit()
    await db_session.refresh(email)

    case = Case(email_id=email.id, status="pending")
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)

    # Mock LLM to avoid real API call
    with patch("app.services.pipeline.llm_explainer.LLMExplainer.explain") as mock_llm:
        mock_llm.return_value = {
            "explanation": "Phishing attempt detected",
            "confidence": 0.95,
        }

        orchestrator = PipelineOrchestrator(db_session)

        # Act
        result = await orchestrator.run_pipeline(case.id)

        # Assert
        assert result["status"] == "completed"
        assert result["final_score"] > 0.7  # High risk
        assert result["stages"]["heuristics"]["completed"] is True
        assert result["stages"]["ml"]["completed"] is True
        assert result["stages"]["llm"]["completed"] is True

@pytest.mark.asyncio
async def test_pipeline_timeout(db_session):
    """Test pipeline timeout handling."""
    email = Email(sender="test@example.com", body="Test")
    case = Case(email_id=email.id, status="pending")
    db_session.add_all([email, case])
    await db_session.commit()

    # Mock LLM to timeout
    with patch("app.services.pipeline.llm_explainer.LLMExplainer.explain") as mock_llm:
        mock_llm.side_effect = asyncio.TimeoutError("LLM timeout")

        orchestrator = PipelineOrchestrator(db_session)

        # Act & Assert
        from app.core.exceptions import PipelineError
        with pytest.raises(PipelineError, match="timeout"):
            await orchestrator.run_pipeline(case.id)
```

### Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.db.session import get_db
from app.models.base import Base

# Test database URL (use SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    """Create test database session."""
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Create test HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    """Mock auth headers (Clerk JWT)."""
    return {
        "Authorization": "Bearer mock-jwt-token",
    }
```

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_heuristics.py

# Run specific test
pytest tests/unit/test_heuristics.py::test_check_suspicious_sender

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run in parallel (faster)
pytest -n auto

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Frontend Testing

### Structure

```
frontend/
├── tests/
│   ├── unit/                  # Vitest
│   │   ├── components/
│   │   │   ├── FormInput.test.ts
│   │   │   └── StatsCard.test.ts
│   │   ├── stores/
│   │   │   ├── cases.test.ts
│   │   │   └── dashboard.test.ts
│   │   └── composables/
│   │       └── useAuth.test.ts
│   └── e2e/                   # Playwright
│       ├── login.spec.ts
│       ├── dashboard.spec.ts
│       └── cases.spec.ts
├── vitest.config.ts
└── playwright.config.ts
```

### Setup

**Install test dependencies:**
```bash
cd frontend
npm install -D vitest @vue/test-utils jsdom @vitest/coverage-v8
npm install -D @playwright/test
```

**Configure Vitest:**
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{ts,vue}'],
      exclude: ['src/main.ts', 'src/**/*.d.ts'],
      thresholds: {
        lines: 30,
        functions: 30,
        branches: 30,
        statements: 30,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Writing Unit Tests (Vitest)

#### Example: Testing Component

```typescript
// tests/unit/components/FormInput.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FormInput from '@/components/common/FormInput.vue'

describe('FormInput', () => {
  it('should render label', () => {
    const wrapper = mount(FormInput, {
      props: {
        modelValue: '',
        label: 'Email Address',
      },
    })

    expect(wrapper.text()).toContain('Email Address')
  })

  it('should emit update:modelValue on input', async () => {
    const wrapper = mount(FormInput, {
      props: {
        modelValue: '',
        label: 'Test',
      },
    })

    const input = wrapper.find('input')
    await input.setValue('new value')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['new value'])
  })

  it('should show error message', () => {
    const wrapper = mount(FormInput, {
      props: {
        modelValue: '',
        label: 'Email',
        error: 'Invalid email format',
      },
    })

    expect(wrapper.text()).toContain('Invalid email format')
    expect(wrapper.classes()).toContain('error')
  })

  it('should be disabled when disabled prop is true', () => {
    const wrapper = mount(FormInput, {
      props: {
        modelValue: '',
        label: 'Test',
        disabled: true,
      },
    })

    const input = wrapper.find('input')
    expect(input.attributes('disabled')).toBeDefined()
  })
})
```

#### Example: Testing Pinia Store

```typescript
// tests/unit/stores/cases.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCasesStore } from '@/stores/cases'
import * as caseService from '@/services/caseService'

vi.mock('@/services/caseService')

describe('Cases Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should fetch cases successfully', async () => {
    const mockData = {
      items: [
        { id: '1', status: 'pending', final_score: 0.5 },
        { id: '2', status: 'resolved', final_score: 0.2 },
      ],
      total: 2,
    }

    vi.mocked(caseService.fetchCases).mockResolvedValue(mockData)

    const store = useCasesStore()
    await store.fetch()

    expect(store.cases).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should handle fetch error', async () => {
    vi.mocked(caseService.fetchCases).mockRejectedValue(new Error('Network error'))

    const store = useCasesStore()
    await store.fetch()

    expect(store.cases).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Network error')
  })

  it('should filter quarantined cases', async () => {
    const mockData = {
      items: [
        { id: '1', status: 'quarantined', final_score: 0.9 },
        { id: '2', status: 'resolved', final_score: 0.2 },
        { id: '3', status: 'quarantined', final_score: 0.8 },
      ],
      total: 3,
    }

    vi.mocked(caseService.fetchCases).mockResolvedValue(mockData)

    const store = useCasesStore()
    await store.fetch()

    expect(store.quarantined).toHaveLength(2)
    expect(store.quarantined.every(c => c.status === 'quarantined')).toBe(true)
  })
})
```

#### Example: Testing Composable

```typescript
// tests/unit/composables/useAuth.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuth } from '@/composables/useAuth'
import { useClerk } from '@clerk/vue'

vi.mock('@clerk/vue')

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return user when authenticated', () => {
    vi.mocked(useClerk).mockReturnValue({
      user: {
        id: 'user_123',
        primaryEmailAddress: { emailAddress: 'test@strike.sh' },
      },
      isLoaded: true,
      isSignedIn: true,
    } as any)

    const { user, isAuthenticated } = useAuth()

    expect(isAuthenticated.value).toBe(true)
    expect(user.value?.id).toBe('user_123')
  })

  it('should return null when not authenticated', () => {
    vi.mocked(useClerk).mockReturnValue({
      user: null,
      isLoaded: true,
      isSignedIn: false,
    } as any)

    const { user, isAuthenticated } = useAuth()

    expect(isAuthenticated.value).toBe(false)
    expect(user.value).toBeNull()
  })
})
```

### Writing E2E Tests (Playwright)

#### Example: Login Flow

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Login Flow', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Should redirect to Clerk login
    await expect(page).toHaveURL(/accounts\.clerk\./)

    // Fill login form
    await page.fill('input[name="identifier"]', 'test@strike.sh')
    await page.click('button:has-text("Continue")')

    await page.fill('input[name="password"]', 'TestPassword123!')
    await page.click('button:has-text("Continue")')

    // Should redirect to dashboard
    await expect(page).toHaveURL('http://localhost:3000/dashboard')
    await expect(page.locator('h1')).toHaveText('Dashboard')
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000')

    await page.fill('input[name="identifier"]', 'invalid@example.com')
    await page.click('button:has-text("Continue")')

    await page.fill('input[name="password"]', 'WrongPassword')
    await page.click('button:has-text("Continue")')

    await expect(page.locator('.error-message')).toBeVisible()
  })
})
```

#### Example: Dashboard

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:3000')
    // ... login steps
  })

  test('should display KPIs', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard')

    await expect(page.locator('[data-testid="total-emails"]')).toBeVisible()
    await expect(page.locator('[data-testid="quarantined-count"]')).toBeVisible()
    await expect(page.locator('[data-testid="avg-score"]')).toBeVisible()
  })

  test('should filter by date range', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard')

    await page.click('[data-testid="date-filter"]')
    await page.click('text=Last 7 days')

    await expect(page.locator('[data-testid="stats-card"]')).toContainText('Last 7 days')
  })
})
```

### Running Tests

```bash
cd frontend

# Run all unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode (for development)
npm run test:watch

# Run specific test file
npm run test tests/unit/components/FormInput.test.ts

# Run E2E tests
npm run test:e2e

# Run E2E in headed mode (see browser)
npm run test:e2e -- --headed

# Run E2E in specific browser
npm run test:e2e -- --project=firefox
```

---

## CI/CD Tests

### GitHub Actions Workflow

Tests se ejecutan automáticamente en cada push y PR.

**Backend workflow:**
```yaml
# .github/workflows/backend-test.yml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-fail-under=60

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
```

**Frontend workflow:**
```yaml
# .github/workflows/frontend-test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright install --with-deps
          npm run test:e2e
```

### Coverage Enforcement

**Backend:** Deploy bloqueado si coverage <60%
```bash
pytest --cov=app --cov-fail-under=60
```

**Frontend:** Warning si coverage <30%
```bash
vitest --coverage --coverage.thresholds.lines=30
```

---

## Best Practices

### General

1. **Arrange-Act-Assert (AAA) pattern**
   ```python
   def test_example():
       # Arrange: setup test data
       user = User(email="test@example.com")

       # Act: execute code under test
       result = user.validate()

       # Assert: verify outcome
       assert result is True
   ```

2. **One assertion per test (idealmente)**
   - Excepción: múltiples assertions del mismo concepto
   - Mejor tener 3 tests pequeños que 1 test grande

3. **Test names should be descriptive**
   - ✅ `test_list_cases_returns_paginated_results`
   - ❌ `test_cases`

4. **Use fixtures for setup**
   - Evita código duplicado
   - Hace tests más legibles

5. **Mock external dependencies**
   - No hacer llamadas reales a APIs externas (OpenAI, Clerk)
   - Usar `unittest.mock` o `pytest-mock`

### Backend-specific

1. **Use async tests for async code**
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       result = await my_async_function()
       assert result is not None
   ```

2. **Isolate database tests**
   - Cada test debe crear su propia data
   - Usar transactions + rollback en fixtures

3. **Test error cases**
   ```python
   with pytest.raises(NotFoundError):
       await service.get_nonexistent()
   ```

### Frontend-specific

1. **Test user interactions, not implementation**
   ```typescript
   // ✅ Good
   await wrapper.find('button').trigger('click')
   expect(wrapper.emitted('submit')).toBeTruthy()

   // ❌ Bad
   expect(wrapper.vm.internalState).toBe(true)
   ```

2. **Use data-testid for stable selectors**
   ```vue
   <button data-testid="submit-button">Submit</button>
   ```
   ```typescript
   await page.click('[data-testid="submit-button"]')
   ```

3. **Mock API calls in unit tests**
   ```typescript
   vi.mock('@/services/api')
   ```

---

## Debugging Failed Tests

### Backend

```bash
# Run single test with verbose output
pytest tests/unit/test_heuristics.py::test_check_suspicious_sender -vv

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show locals on failure
pytest --showlocals
```

### Frontend

```bash
# Run single test
npm run test -- FormInput.test.ts

# Debug in VSCode
# Add to .vscode/launch.json:
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "test:debug"],
}
```

---

## Resources

- [pytest docs](https://docs.pytest.org/)
- [Vitest docs](https://vitest.dev/)
- [Playwright docs](https://playwright.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Testing Pinia](https://pinia.vuejs.org/cookbook/testing.html)

---

## Makefile Shortcuts

```bash
# Run all tests (backend + frontend)
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run with coverage
make test-coverage

# Run E2E tests
make test-e2e
```

Ver [CONTRIBUTING.md](../CONTRIBUTING.md) para workflow completo.
