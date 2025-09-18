# Testing

In React and Next.js, there are a few different types of tests you can write, each with its own purpose and use cases. This page provides an overview of types and commonly used tools you can use to test your application.

## Types of Tests

- **Unit Testing** involves testing individual units (or blocks of code) in isolation. In React, a unit can be a single function, hook, or component.
- **Component Testing** is a more focused version of unit testing where the primary subject of the tests is React components. This may involve testing how components are rendered, their interaction with props, and their behavior in response to user events.
- **Integration Testing** involves testing how multiple units work together. This can be a combination of components, hooks, and functions.
- **End-to-End (E2E) Testing** involves testing user flows in an environment that simulates real user scenarios, like the browser. This means testing specific tasks (e.g. signup flow) in a production-like environment.
- **Snapshot Testing** involves capturing the rendered output of a component and saving it to a snapshot file. When tests run, the current rendered output of the component is compared against the saved snapshot. Changes in the snapshot are used to indicate unexpected changes in behavior.

## Async Server Components

Since `async` Server Components are new to the React ecosystem, some tools do not fully support them. In the meantime, we recommend using End-to-End Testing over Unit Testing for `async` components.

## Guides

See the guides below to learn how to set up Next.js with these commonly used testing tools:

- **Cypress**: Learn how to set up Cypress with Next.js for End-to-End (E2E) and Component Testing.
- **Jest**: Learn how to set up Jest with Next.js for Unit Testing and Snapshot Testing.
- **Playwright**: Learn how to set up Playwright with Next.js for End-to-End (E2E) Testing.
- **Vitest**: Learn how to set up Vitest with Next.js for Unit Testing.

## Setting Up Testing Tools

### Jest

Jest is a popular testing framework that provides a complete testing solution out of the box. It includes a test runner, assertion library, and mocking utilities.

#### Installation

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
# or
yarn add --dev jest @testing-library/react @testing-library/jest-dom
# or
pnpm add --save-dev jest @testing-library/react @testing-library/jest-dom
```

#### Configuration

Create a `jest.config.js` file in your project root:

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    // Handle module aliases (this will be automatically configured for you based on your tsconfig.json paths)
    '^@/(.*)$': '<rootDir>/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
```

Create a `jest.setup.js` file:

```javascript
import '@testing-library/jest-dom'
```

#### Writing Tests

```javascript
import { render, screen } from '@testing-library/react'
import Page from './page'

describe('Page', () => {
  it('renders a heading', () => {
    render(<Page />)

    const heading = screen.getByRole('heading', { level: 1 })

    expect(heading).toBeInTheDocument()
  })
})
```

### Vitest

Vitest is a fast testing framework powered by Vite. It's designed to be a drop-in replacement for Jest with better performance and a more modern developer experience.

#### Installation

```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
# or
yarn add --dev vitest @testing-library/react @testing-library/jest-dom jsdom
# or
pnpm add --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

#### Configuration

Update your `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

Create a `vitest.config.js` file:

```javascript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './test/setup.js',
  },
})
```

Create a `test/setup.js` file:

```javascript
import '@testing-library/jest-dom'
```

### Cypress

Cypress is an end-to-end testing framework that runs in the browser. It's great for testing user flows and integration scenarios.

#### Installation

```bash
npm install --save-dev cypress
# or
yarn add --dev cypress
# or
pnpm add --save-dev cypress
```

#### Setup

```bash
npx cypress open
```

This will create a `cypress` folder with example tests. Update your `cypress.config.js`:

```javascript
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    baseUrl: 'http://localhost:3000',
  },
  component: {
    devServer: {
      framework: 'next',
      bundler: 'webpack',
    },
  },
})
```

#### Writing E2E Tests

```javascript
describe('Navigation', () => {
  it('should navigate to the about page', () => {
    // Start from the index page
    cy.visit('http://localhost:3000/')

    // Find a link with an href attribute containing "about" and click it
    cy.get('a[href*="about"]').click()

    // The new url should include "/about"
    cy.url().should('include', '/about')

    // The new page should contain an h1 with "About"
    cy.get('h1').contains('About')
  })
})
```

#### Component Testing

```javascript
import { mount } from 'cypress/react18'
import Button from './Button'

describe('<Button />', () => {
  it('renders', () => {
    // mount the component under test
    mount(<Button>Click me</Button>)

    // assert that the component renders with the correct text
    cy.get('button').should('contain', 'Click me')
  })
})
```

### Playwright

Playwright is a cross-browser automation library that can be used for end-to-end testing. It supports multiple browsers and provides powerful debugging capabilities.

#### Installation

```bash
npm install --save-dev @playwright/test
# or
yarn add --dev @playwright/test
# or
pnpm add --save-dev @playwright/test
```

#### Setup

```bash
npx playwright install
```

#### Configuration

Create a `playwright.config.js` file:

```javascript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

#### Writing Tests

```javascript
import { test, expect } from '@playwright/test'

test('has title', async ({ page }) => {
  await page.goto('https://playwright.dev/')

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Playwright/)
})

test('get started link', async ({ page }) => {
  await page.goto('https://playwright.dev/')

  // Click the get started link.
  await page.getByRole('link', { name: 'Get started' }).click()

  // Expects the URL to contain intro.
  await expect(page).toHaveURL(/.*intro/)
})
```

## Testing Best Practices

### Unit Testing

- Test individual functions, hooks, and components in isolation
- Mock external dependencies and API calls
- Focus on testing the logic and behavior of the unit
- Use descriptive test names that explain what is being tested

### Component Testing

- Test component rendering with different props
- Test user interactions (clicks, form submissions, etc.)
- Test component state changes
- Use testing-library utilities for accessible queries

### Integration Testing

- Test how multiple components work together
- Test data flow between components
- Test API integrations
- Mock external services when necessary

### E2E Testing

- Test complete user workflows
- Test in a production-like environment
- Cover critical user journeys
- Use realistic test data

### Snapshot Testing

- Use for testing component UI consistency
- Review snapshot changes carefully
- Update snapshots when UI changes are intentional
- Don't rely solely on snapshots for testing logic

## Running Tests

### Jest/Vitest

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- path/to/test.js
```

### Cypress

```bash
# Open Cypress Test Runner
npx cypress open

# Run tests headlessly
npx cypress run

# Run specific test file
npx cypress run --spec "cypress/integration/sample.spec.js"
```

### Playwright

```bash
# Run all tests
npx playwright test

# Run tests in UI mode
npx playwright test --ui

# Run specific test
npx playwright test example.spec.js

# Generate test
npx playwright codegen localhost:3000
```

## Continuous Integration

Set up your testing in CI to run automatically on every push and pull request:

### GitHub Actions Example

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
      - run: npm run build
```

## Next Steps

Learn more about testing strategies and best practices in the React Testing Library documentation and the testing tools' official documentation.
