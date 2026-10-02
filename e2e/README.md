# E2E Tests (Playwright)

## Prerequisites
- Node.js 18+
- Frontend running on http://localhost:3000
- Backend running on http://localhost:8000

## Setup
```bash
cd e2e
npm install
npx playwright install chromium
```

## Run
```bash
npx playwright test              # headless
npx playwright test --headed     # headed (GUI)
npx playwright test --ui         # Playwright UI mode
npx playwright show-report       # view HTML report
```

## Tests
- `user-journey.spec.ts`: Full user journey (register → create todo → toggle → logout)
- `cross-user-isolation.spec.ts`: User A data not visible to User B
