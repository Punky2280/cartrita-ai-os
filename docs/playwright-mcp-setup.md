# Playwright MCP Configuration Setup

This document describes the Playwright Model Context Protocol (MCP) configuration for the Cartrita AI OS project.

## Installation Complete

The following components have been installed and configured:

### 1. Playwright Dependencies
- `@playwright/test`: Playwright test runner
- `playwright`: Playwright library
- `@automatalabs/mcp-server-playwright`: MCP server for Playwright integration

### 2. Configuration Files

#### `.mcp.json`
MCP server configuration file that defines the Playwright server:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "node",
      "args": ["node_modules/@automatalabs/mcp-server-playwright/dist/index.js"],
      "env": {
        "HEADLESS": "false",
        "BROWSER": "chromium",
        "VIEWPORT_WIDTH": "1280",
        "VIEWPORT_HEIGHT": "720"
      }
    }
  }
}
```

#### `playwright.config.ts`
Playwright test configuration with support for:
- Multiple browsers (Chromium, Firefox, WebKit)
- Mobile viewports
- Automatic server startup
- Test artifacts (traces, screenshots, videos)

#### `.claude/settings.local.json`
Updated Claude settings to:
- Enable the Playwright MCP server
- Add permissions for Playwright commands

### 3. Test Structure

Tests are located in `tests/e2e/` directory with the following example tests:
- Basic page loading tests
- Navigation element tests
- Responsive design tests
- API connection tests
- Voice interface tests
- Settings panel tests

### 4. Available Scripts

The following npm scripts have been added:
- `npm run test:e2e` - Run all E2E tests
- `npm run test:e2e:ui` - Run tests with interactive UI
- `npm run test:e2e:debug` - Run tests in debug mode
- `npm run test:e2e:headed` - Run tests with visible browser
- `npm run playwright:install` - Install Playwright browsers
- `npm run playwright:report` - Show test report

## System Dependencies

**Note:** Playwright requires system dependencies that need to be installed with sudo access:

```bash
# Install system dependencies (requires sudo)
npx playwright install-deps
```

Alternatively, run in Docker or use the provided container environment.

## Usage

### Running Tests

1. Basic test run:
```bash
npm run test:e2e
```

2. Interactive UI mode:
```bash
npm run test:e2e:ui
```

3. Debug mode:
```bash
npm run test:e2e:debug
```

### MCP Server Usage

The MCP server allows Claude to interact with Playwright for browser automation tasks. When enabled, Claude can:
- Navigate web pages
- Interact with page elements
- Take screenshots
- Execute JavaScript in the browser context
- Perform automated testing

### Environment Variables

You can customize the MCP server behavior using environment variables in `.mcp.json`:
- `HEADLESS`: Set to "true" for headless mode
- `BROWSER`: Choose browser (chromium, firefox, webkit)
- `VIEWPORT_WIDTH`: Set browser viewport width
- `VIEWPORT_HEIGHT`: Set browser viewport height

## Troubleshooting

1. **Missing system dependencies**: Run `npx playwright install-deps` with sudo access
2. **Browser installation issues**: Run `npx playwright install` to reinstall browsers
3. **MCP server not working**: Restart Claude Code to reload the MCP configuration

## Next Steps

1. Install system dependencies when sudo access is available
2. Write application-specific E2E tests
3. Integrate with CI/CD pipeline
4. Configure test reporting and monitoring