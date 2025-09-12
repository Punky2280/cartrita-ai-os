// Conditional Playwright import to avoid type errors if playwright not installed locally
let test: any, expect: any
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  ({ test, expect } = require('@playwright/test'))
} catch {
  test = (name: string, fn: () => Promise<void>) => {
    console.warn('Playwright not available, skipping test:', name)
  }
  expect = () => ({ toBe: () => undefined })
}

test('PWA manifest and service worker', async ({ page }) => {
  await page.goto('/')
  // Check manifest
  const manifest = await page.evaluate(() => {
    return fetch('/manifest.webmanifest').then(r => r.json())
  })
  expect(manifest.name).toContain('Cartrita')
  // Check service worker
  const sw = await page.evaluate(() => navigator.serviceWorker?.getRegistration())
  expect(sw).not.toBeNull()
})

test('Theme toggling persists', async ({ page }) => {
  await page.goto('/')
  const btn = await page.getByRole('button', { name: /theme/i })
  await btn.click()
  await btn.click()
  // Should persist in localStorage
  const theme = await page.evaluate(() => localStorage.getItem('theme'))
  expect(theme).toBeTruthy()
})
