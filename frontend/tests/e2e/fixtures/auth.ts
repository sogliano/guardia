import { test as base, Page } from '@playwright/test'

type TestFixtures = {
  authenticatedPage: Page
}

export const test = base.extend<TestFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/')

    // Mock Clerk authentication in test environment
    // This assumes Clerk test mode or mock implementation
    await page.evaluate(() => {
      localStorage.setItem('__clerk_test_token', 'test_token_123')
      localStorage.setItem('__clerk_session', JSON.stringify({
        userId: 'user_test123',
        sessionId: 'sess_test123',
      }))
    })

    // Wait for potential redirect to dashboard
    await page.waitForTimeout(1000)

    await use(page)

    // Cleanup
    await page.evaluate(() => {
      localStorage.clear()
    })
  },
})

export { expect } from '@playwright/test'
