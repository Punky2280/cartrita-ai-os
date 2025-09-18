// Conditional Playwright import to avoid type errors if playwright not installed locally
// Removed redeclaration of Vitest globals (test, expect) which are provided automatically
let playwrightTest: any, playwrightExpect: any
try {

  ({ test: playwrightTest, expect: playwrightExpect } = require('@playwright/test'))
} catch {}

const maybe = (name: string, fn: (ctx: any) => Promise<void>) => {
  if (!playwrightTest) {
    console.warn('Playwright not available, skipping test:', name)
    return
  }
  playwrightTest(name, fn)
}

maybe('PWA manifest and service worker', async ({ page }) => {
  await page.goto('/')
  // Check manifest
  const manifest = await page.evaluate(() => {
    return fetch('/manifest.webmanifest').then(r => r.json())
  })
  playwrightExpect(manifest.name).toContain('Cartrita')
  // Check service worker
  const sw = await page.evaluate(() => navigator.serviceWorker?.getRegistration())
  playwrightExpect(sw).not.toBeNull()
})

maybe('Theme toggling persists', async ({ page }) => {
  await page.goto('/')
  const btn = await page.getByRole('button', { name: /theme/i })
  await btn.click()
  await btn.click()
  // Should persist in localStorage
  const theme = await page.evaluate(() => localStorage.getItem('theme'))
  playwrightExpect(theme).toBeTruthy()
})
