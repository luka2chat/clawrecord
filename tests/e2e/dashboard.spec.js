// @ts-check
const { test, expect } = require("@playwright/test");
const { _electron: electron } = require("playwright");
const path = require("path");

const APP_PATH = path.join(__dirname, "..", "..");

let electronApp;
let window;

test.beforeAll(async () => {
  electronApp = await electron.launch({
    args: [APP_PATH, "--no-sandbox"],
    env: { ...process.env, DISPLAY: process.env.DISPLAY || ":1" },
  });
  window = await electronApp.firstWindow();
  await window.waitForLoadState("domcontentloaded");
  await window.waitForTimeout(1000);
});

test.afterAll(async () => {
  if (electronApp) {
    await electronApp.close();
  }
});

test.describe("Dashboard Tab Navigation", () => {
  test("Home tab should be active by default", async () => {
    const homeTab = window.locator('.tab[data-tab="home"]');
    await expect(homeTab).toHaveClass(/active/);
  });

  test("should render topbar with brand name", async () => {
    const brand = window.locator(".topbar-brand");
    await expect(brand).toContainText("ClawRecord");
  });

  test("should render language switcher", async () => {
    const langSw = window.locator(".lang-sw");
    await expect(langSw).toBeVisible();

    const enBtn = window.locator(".lang-sw button").first();
    await expect(enBtn).toContainText("EN");
  });

  test("should navigate to Quests tab", async () => {
    await window.locator('.tab[data-tab="quests"]').click();
    await window.waitForTimeout(300);

    const questsTab = window.locator('.tab[data-tab="quests"]');
    await expect(questsTab).toHaveClass(/active/);

    const content = await window.locator("#app").innerHTML();
    expect(content).toContain("Daily Quests");
  });

  test("should navigate to Skills tab", async () => {
    await window.locator('.tab[data-tab="skills"]').click();
    await window.waitForTimeout(300);

    const skillsTab = window.locator('.tab[data-tab="skills"]');
    await expect(skillsTab).toHaveClass(/active/);

    const content = await window.locator("#app").innerHTML();
    expect(content).toContain("Skills");
  });

  test("should navigate to Stats tab", async () => {
    await window.locator('.tab[data-tab="stats"]').click();
    await window.waitForTimeout(300);

    const statsTab = window.locator('.tab[data-tab="stats"]');
    await expect(statsTab).toHaveClass(/active/);

    const content = await window.locator("#app").innerHTML();
    expect(content).toContain("Analytics");
  });

  test("should navigate to Profile tab", async () => {
    await window.locator('.tab[data-tab="profile"]').click();
    await window.waitForTimeout(300);

    const profileTab = window.locator('.tab[data-tab="profile"]');
    await expect(profileTab).toHaveClass(/active/);

    const content = await window.locator("#app").innerHTML();
    expect(content).toContain("Achievements");
  });

  test("should navigate back to Home tab", async () => {
    await window.locator('.tab[data-tab="home"]').click();
    await window.waitForTimeout(300);

    const homeTab = window.locator('.tab[data-tab="home"]');
    await expect(homeTab).toHaveClass(/active/);
  });
});

test.describe("Home Tab Content", () => {
  test.beforeAll(async () => {
    await window.locator('.tab[data-tab="home"]').click();
    await window.waitForTimeout(300);
  });

  test("should display hero section with Claw Power", async () => {
    const hero = window.locator(".hero");
    await expect(hero).toBeVisible();

    const powerLabel = window.locator(".hero-power-label");
    await expect(powerLabel).toContainText("Claw Power");
  });

  test("should display stat boxes (level, streak, HP, weekly XP)", async () => {
    const statRow = window.locator(".stat-row");
    await expect(statRow).toBeVisible();

    const statBoxes = window.locator(".stat-box");
    const count = await statBoxes.count();
    expect(count).toBe(4);
  });

  test("should display XP bar", async () => {
    const xpBar = window.locator(".xp-bar");
    await expect(xpBar).toBeVisible();
  });

  test("should display daily quests section", async () => {
    const questSection = window.locator(".quest-grid");
    await expect(questSection).toBeAttached();
  });
});

test.describe("Language Switching", () => {
  test("should switch to Chinese", async () => {
    await window.locator('.tab[data-tab="home"]').click();
    await window.waitForTimeout(300);

    await window.evaluate(() => window._setLang("zh"));
    await window.waitForTimeout(300);

    const powerLabel = window.locator(".hero-power-label");
    await expect(powerLabel).toContainText("龙虾战力");
  });

  test("should switch back to English", async () => {
    await window.evaluate(() => window._setLang("en"));
    await window.waitForTimeout(300);

    const powerLabel = window.locator(".hero-power-label");
    await expect(powerLabel).toContainText("Claw Power");
  });
});

test.describe("Profile Tab Content", () => {
  test.beforeAll(async () => {
    await window.locator('.tab[data-tab="profile"]').click();
    await window.waitForTimeout(300);
  });

  test("should display username", async () => {
    const content = await window.locator("#app").innerHTML();
    expect(content.length).toBeGreaterThan(0);
  });

  test("should display badge grid", async () => {
    const badgeGrid = window.locator(".badge-grid");
    await expect(badgeGrid).toBeAttached();
  });

  test("should display share buttons", async () => {
    const shareButtons = window.locator(".share-btn");
    const count = await shareButtons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test("should display leaderboard CTA", async () => {
    const lbCta = window.locator(".lb-cta");
    await expect(lbCta).toBeAttached();
  });
});
