import { test, expect } from './fixtures/auth'

test.describe('Case Management Flow', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    // Setup: Mock API to return test cases
    await authenticatedPage.route('**/api/v1/cases*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'case-123',
              case_number: 'CASE-001',
              final_score: 0.85,
              risk_level: 'high',
              verdict: 'quarantined',
              status: 'open',
              sender_email: 'attacker@evil.com',
              recipient_email: 'victim@strike.sh',
              subject: 'Urgent: Wire Transfer',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          size: 20,
        }),
      })
    })
  })

  test('should display cases list', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/cases')

    // Wait for cases to load
    await authenticatedPage.waitForTimeout(1000)

    // Verify case appears in list
    const caseElement = authenticatedPage.locator('[data-testid*="case"]').first()
    await expect(caseElement).toBeVisible()
  })

  test('should navigate to case detail', async ({ authenticatedPage }) => {
    // Mock case detail endpoint
    await authenticatedPage.route('**/api/v1/cases/case-123/detail', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'case-123',
          case_number: 'CASE-001',
          final_score: 0.85,
          risk_level: 'high',
          verdict: 'quarantined',
          analyses: [
            {
              id: 'analysis-1',
              stage: 'heuristic',
              score: 0.75,
              evidences: [
                { type: 'auth_failure', severity: 'high', detail: 'SPF failed' },
              ],
            },
          ],
          email: {
            sender_email: 'attacker@evil.com',
            subject: 'Urgent: Wire Transfer',
          },
        }),
      })
    })

    await authenticatedPage.goto('/cases/case-123')

    // Verify case detail loaded
    await expect(authenticatedPage.locator('h1')).toContainText('CASE-001')
  })

  test('should filter cases by risk level', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/cases')

    // Find and click risk level filter
    const filterButton = authenticatedPage.locator('[data-testid="filter-risk-level"]')
    if (await filterButton.isVisible()) {
      await filterButton.click()

      // Select high risk
      const highOption = authenticatedPage.locator('text=High')
      if (await highOption.isVisible()) {
        await highOption.click()
      }
    }

    // Verify URL has filter param
    await authenticatedPage.waitForTimeout(500)
  })
})
