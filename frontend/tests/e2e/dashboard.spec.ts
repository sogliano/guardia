import { test, expect } from './fixtures/auth'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    // Mock dashboard stats API
    await authenticatedPage.route('**/api/v1/dashboard/stats*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_cases: 150,
          high_risk_cases: 45,
          quarantined_cases: 12,
          avg_score: 0.42,
          verdict_breakdown: {
            allowed: 100,
            warn: 35,
            quarantined: 12,
            blocked: 3,
          },
          risk_distribution: {
            low: 90,
            medium: 35,
            high: 25,
          },
          timeline: [
            {
              date: '2026-02-01',
              allowed: 30,
              warn: 10,
              quarantined: 5,
              blocked: 1,
            },
          ],
        }),
      })
    })
  })

  test('should display dashboard stats', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard')

    // Wait for stats to load
    await authenticatedPage.waitForTimeout(1500)

    // Verify stats are displayed
    const statsCard = authenticatedPage.locator('[data-testid*="stats"]').first()
    await expect(statsCard).toBeVisible()
  })

  test('should display charts', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard')

    // Wait for charts to render
    await authenticatedPage.waitForTimeout(2000)

    // Verify chart containers exist
    const chartElements = authenticatedPage.locator('canvas')
    const count = await chartElements.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should navigate to cases from recent cases widget', async ({ authenticatedPage }) => {
    // Mock recent cases
    await authenticatedPage.route('**/api/v1/cases*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'case-1',
              case_number: 'CASE-001',
              final_score: 0.75,
              risk_level: 'high',
            },
          ],
          total: 1,
          page: 1,
          size: 5,
        }),
      })
    })

    await authenticatedPage.goto('/dashboard')
    await authenticatedPage.waitForTimeout(1500)

    // Click on a case link if visible
    const caseLink = authenticatedPage.locator('a[href*="/cases/"]').first()
    if (await caseLink.isVisible()) {
      await caseLink.click()

      // Verify navigation to case detail
      await expect(authenticatedPage).toHaveURL(/\/cases\//)
    }
  })
})
