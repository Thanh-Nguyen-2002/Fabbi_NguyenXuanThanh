import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';

/**
 * Helper: register a new user then login, returns the authenticated page.
 */
async function registerAndLogin(
  context: BrowserContext,
  email: string,
  password: string
): Promise<Page> {
  const page = await context.newPage();

  // Register
  await page.goto('/register');
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /register/i }).click();

  // Wait until redirected away from /register
  await page.waitForURL((url) =>
    !url.pathname.includes('/register') && !url.pathname.includes('/login')
  );

  return page;
}

test.describe('Scenario 2: Cross-User Data Isolation', () => {
  test('user A todos not visible to user B', async ({ browser }: { browser: Browser }) => {
    const timestamp = Date.now();
    const emailA = `test_a+${timestamp}@example.com`;
    const emailB = `test_b+${timestamp + 1}@example.com`;
    const password = 'Password123!';

    // --- User A: register, login, create a todo ---
    const contextA = await browser.newContext();
    const pageA = await registerAndLogin(contextA, emailA, password);

    await pageA.getByRole('button', { name: /add todo/i }).click();
    const titleInputA = pageA.getByLabel(/title/i).or(pageA.getByPlaceholder(/title/i));
    await titleInputA.fill('User A Secret Todo');
    await pageA.getByRole('button', { name: /create|submit|add/i }).click();

    // Verify todo visible in User A's dashboard
    await expect(pageA.getByText('User A Secret Todo')).toBeVisible();

    // --- User B: register + login in a completely isolated context ---
    const contextB = await browser.newContext();
    const pageB = await registerAndLogin(contextB, emailB, password);

    // Navigate to dashboard (already there after registration)
    // Wait for the todo list area to load before asserting
    await pageB.waitForLoadState('networkidle');

    // Verify User A's todo does NOT appear in User B's list
    await expect(pageB).not.toContainText('User A Secret Todo');

    // Cleanup
    await contextA.close();
    await contextB.close();
  });
});
