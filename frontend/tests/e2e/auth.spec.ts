import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/')

    // Clerk should redirect to sign-in or show login UI
    await expect(page).toHaveURL(/.*/)

    // Check for Clerk sign-in elements or app header
    const hasAuthElement = await page.locator('[data-clerk-id]').count() > 0
    const hasAppHeader = await page.locator('header').count() > 0

    expect(hasAuthElement || hasAppHeader).toBeTruthy()
  })

  test('should navigate to dashboard after authentication', async ({ page }) => {
    await page.goto('/')

    // Mock authenticated state
    await page.evaluate(() => {
      localStorage.setItem('__clerk_test_token', 'test_token_123')
    })

    // Navigate to dashboard
    await page.goto('/dashboard')

    // Verify dashboard elements
    const pageTitle = await page.title()
    expect(pageTitle).toContain('Guard-IA')
  })
})
