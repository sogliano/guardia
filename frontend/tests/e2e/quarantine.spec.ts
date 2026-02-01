import { test, expect } from './fixtures/auth'

test.describe('Quarantine Management', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    // Mock quarantine cases API
    await authenticatedPage.route('**/api/v1/cases*', async (route) => {
      const url = new URL(route.request().url())
      const verdict = url.searchParams.get('verdict')

      if (verdict === 'quarantined') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'quarantine-123',
                case_number: 'CASE-Q001',
                final_score: 0.9,
                risk_level: 'high',
                verdict: 'quarantined',
                status: 'quarantined',
                sender_email: 'phishing@evil.com',
                subject: 'Urgent Account Verification',
              },
            ],
            total: 1,
            page: 1,
            size: 20,
          }),
        })
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [],
            total: 0,
            page: 1,
            size: 20,
          }),
        })
      }
    })
  })

  test('should display quarantined emails', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/quarantine')

    // Wait for quarantine list to load
    await authenticatedPage.waitForTimeout(1000)

    // Verify quarantined email appears
    const emailElement = authenticatedPage.locator('[data-testid*="quarantine"]').first()
    await expect(emailElement).toBeVisible()
  })

  test('should release quarantined email', async ({ authenticatedPage }) => {
    // Mock release endpoint
    await authenticatedPage.route('**/api/v1/quarantine/*/release', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'quarantine-123',
          status: 'released',
        }),
      })
    })

    await authenticatedPage.goto('/quarantine')
    await authenticatedPage.waitForTimeout(1000)

    // Find release button
    const releaseButton = authenticatedPage.locator('[data-testid="release-btn"]').first()
    if (await releaseButton.isVisible()) {
      await releaseButton.click()

      // Confirm release in modal
      const confirmButton = authenticatedPage.locator('button:has-text("Confirm")')
      if (await confirmButton.isVisible()) {
        await confirmButton.click()
      }
    }
  })

  test('should delete quarantined email', async ({ authenticatedPage }) => {
    // Mock delete endpoint
    await authenticatedPage.route('**/api/v1/quarantine/*/delete', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'quarantine-123',
          status: 'deleted',
        }),
      })
    })

    await authenticatedPage.goto('/quarantine')
    await authenticatedPage.waitForTimeout(1000)

    // Find delete button
    const deleteButton = authenticatedPage.locator('[data-testid="delete-btn"]').first()
    if (await deleteButton.isVisible()) {
      await deleteButton.click()

      // Confirm delete
      const confirmButton = authenticatedPage.locator('button:has-text("Delete")')
      if (await confirmButton.isVisible()) {
        await confirmButton.click()
      }
    }
  })
})
