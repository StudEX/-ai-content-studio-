import { test, expect } from '@playwright/test'

test.describe('Naledi Intelligence Platform', () => {
  test('loads command shell on homepage', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=NALEDI')).toBeVisible()
    await expect(page.locator('text=Command Shell')).toBeVisible()
    await expect(page.locator('input[placeholder="Enter command..."]')).toBeVisible()
  })

  test('navigates to agent board', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('text=Agent Board')).toBeVisible()
    await expect(page.locator('text=QUEUED')).toBeVisible()
    await expect(page.locator('text=RUNNING')).toBeVisible()
    await expect(page.locator('text=DONE')).toBeVisible()
    await expect(page.locator('text=ERROR')).toBeVisible()
  })

  test('navigates to model browser', async ({ page }) => {
    await page.goto('/models')
    await expect(page.locator('text=Model Browser')).toBeVisible()
    await expect(page.locator('text=Ollama')).toBeVisible()
    await expect(page.locator('text=fal.ai Video')).toBeVisible()
  })

  test('navigates to token calculator', async ({ page }) => {
    await page.goto('/tokens')
    await expect(page.locator('text=Token Calculator')).toBeVisible()
    await expect(page.locator('text=ZAR')).toBeVisible()
  })

  test('sidebar shows all nav items', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Command Shell')).toBeVisible()
    await expect(page.locator('text=Agent Board')).toBeVisible()
    await expect(page.locator('text=Models')).toBeVisible()
    await expect(page.locator('text=Token Calc')).toBeVisible()
  })

  test('command shell accepts input', async ({ page }) => {
    await page.goto('/')
    const input = page.locator('input[placeholder="Enter command..."]')
    await input.fill('write a headline for Studex Meat')
    await input.press('Enter')
    // Should show the command in the log
    await expect(page.locator('text=write a headline for Studex Meat')).toBeVisible()
  })
})
