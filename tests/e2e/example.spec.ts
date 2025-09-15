import { test, expect } from '@playwright/test';

test.describe('Cartrita AI OS - Basic E2E Tests', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');

    // Check if the page title is present
    await expect(page).toHaveTitle(/Cartrita/i);
  });

  test('should have main navigation elements', async ({ page }) => {
    await page.goto('/');

    // Check for main UI elements
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible();
  });

  test('should be responsive', async ({ page }) => {
    await page.goto('/');

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    const mobileMenu = page.locator('[data-testid="mobile-menu"]');

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    const desktopNav = page.locator('[data-testid="desktop-nav"]');
  });

  test('should handle API connection', async ({ page }) => {
    await page.goto('/');

    // Mock API response
    await page.route('**/api/health', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy' })
      });
    });

    // Check if connection status is displayed
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    await expect(connectionStatus).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Voice Interface Tests', () => {
  test('should display voice controls', async ({ page }) => {
    await page.goto('/');

    // Look for voice interface elements
    const voiceButton = page.locator('[data-testid="voice-button"]');
    await expect(voiceButton).toBeVisible();
  });

  test('should toggle voice recording', async ({ page }) => {
    await page.goto('/');

    const voiceButton = page.locator('[data-testid="voice-button"]');

    // Click to start recording
    await voiceButton.click();
    await expect(voiceButton).toHaveAttribute('aria-pressed', 'true');

    // Click to stop recording
    await voiceButton.click();
    await expect(voiceButton).toHaveAttribute('aria-pressed', 'false');
  });
});

test.describe('Settings Panel Tests', () => {
  test('should open settings panel', async ({ page }) => {
    await page.goto('/');

    // Click settings button
    const settingsButton = page.locator('[data-testid="settings-button"]');
    await settingsButton.click();

    // Check if settings panel is visible
    const settingsPanel = page.locator('[data-testid="settings-panel"]');
    await expect(settingsPanel).toBeVisible();
  });

  test('should save settings', async ({ page }) => {
    await page.goto('/');

    // Open settings
    await page.locator('[data-testid="settings-button"]').click();

    // Change a setting
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    await themeToggle.click();

    // Save settings
    const saveButton = page.locator('[data-testid="save-settings"]');
    await saveButton.click();

    // Verify settings were saved (check localStorage or API call)
    const theme = await page.evaluate(() => localStorage.getItem('theme'));
    expect(theme).toBeTruthy();
  });
});