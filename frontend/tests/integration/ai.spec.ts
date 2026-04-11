import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request, context }) => {
  await request.post("/api/auth/login", {
    data: { username: "user", password: "password" },
  });
  const cookies = (await request.storageState()).cookies;
  await context.addCookies(cookies);
});

test("ai chat creates a card on the board", async ({ page, request }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();

  const ping = await request.get("/api/ai/ping");
  if (ping.status() !== 200) {
    test.skip(true, "AI not available — skipping AI chat e2e test");
    return;
  }

  const chatInput = page.getByPlaceholder("Ask the AI...");
  await chatInput.fill("Add a card titled 'AI E2E Card' to the first column with details 'created by test'.");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.locator("aside").getByText(/done|added|created/i)).toBeVisible({ timeout: 30_000 });
  await expect(firstColumn.getByText("AI E2E Card")).toBeVisible({ timeout: 10_000 });
});
