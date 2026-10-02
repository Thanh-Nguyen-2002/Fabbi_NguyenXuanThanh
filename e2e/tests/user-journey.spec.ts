import { test, expect } from '@playwright/test';

test.describe('Scenario 1: Full User Journey', () => {
  test('full user journey - register, login, create todo, toggle completion, logout', async ({ page }) => {
    const email = `test+${Date.now()}@example.com`;
    const password = 'Password123!';

    // --- Register ---
    await page.goto('/register');
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole('button', { name: /register/i }).click();

    // Wait for redirect away from /register (to dashboard or home)
    await page.waitForURL((url) =>
      !url.pathname.includes('/register') && !url.pathname.includes('/login')
    );
    const urlAfterRegister = page.url();
    expect(urlAfterRegister).not.toContain('/login');
    expect(urlAfterRegister).not.toContain('/register');

    // --- Create Todo ---
    await page.getByRole('button', { name: /add todo/i }).click();

    const titleInput = page.getByLabel(/title/i).or(page.getByPlaceholder(/title/i));
    await titleInput.fill('My E2E Todo');
    await page.getByRole('button', { name: /create|submit|add/i }).click();

    // Verify todo appears in list
    const todoItem = page.getByText('My E2E Todo');
    await expect(todoItem).toBeVisible();

    // --- Toggle Completion ---
    // Click checkbox/toggle next to the todo
    const todoRow = page.locator('li, [data-testid="todo-item"]').filter({ hasText: 'My E2E Todo' });
    const checkbox = todoRow.getByRole('checkbox').or(todoRow.locator('input[type="checkbox"]'));
    await checkbox.click();

    // Verify the todo is marked as completed
    await expect(checkbox.or(todoRow.locator('[aria-checked="true"]'))).toBeChecked().or(
      expect(todoRow.locator('.line-through, [class*="complete"], [class*="done"]')).toBeVisible()
    );

    // --- Logout ---
    await page.getByRole('button', { name: /logout|sign out/i }).click();

    // Verify redirect back to /login
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});
