import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request, context }) => {
  await request.post("/api/auth/login", {
    data: { username: "user", password: "password" },
  });
  // Cookies set on the shared context are used by subsequent page navigations
  const cookies = (await request.storageState()).cookies;
  await context.addCookies(cookies);
});

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("add card persists after reload", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Persist me");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Persist me")).toBeVisible();

  await page.reload();
  await expect(firstColumn.getByText("Persist me")).toBeVisible();
});

test("column rename persists after reload", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const input = firstColumn.getByLabel("Column title");
  await input.fill("Renamed Column");
  await input.blur();
  await page.reload();
  await expect(
    page.locator('[data-testid^="column-"]').first().getByLabel("Column title")
  ).toHaveValue("Renamed Column");
});

test("login and logout flow", async ({ page, context }) => {
  // Clear the session cookie to test login from scratch
  await context.clearCookies();
  await page.goto("/");
  // Should redirect to login
  await expect(page).toHaveURL(/\/login/);
  // Fill in credentials and submit
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  // Should land on the board
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  // Logout
  await page.getByRole("button", { name: /sign out/i }).click();
  // Should redirect back to login
  await expect(page).toHaveURL(/\/login/);
});
