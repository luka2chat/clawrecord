// @ts-check
const { test, expect } = require("@playwright/test");
const { _electron: electron } = require("playwright");
const path = require("path");
const fs = require("fs");

const APP_PATH = path.join(__dirname, "..", "..");
const DATA_JS = path.join(APP_PATH, "docs", "data.js");
const DATA_JS_BACKUP = DATA_JS + ".test-backup";

let electronApp;
let window;

test.describe("Setup Screen (no data)", () => {
  test.beforeAll(async () => {
    if (fs.existsSync(DATA_JS)) {
      fs.renameSync(DATA_JS, DATA_JS_BACKUP);
    }

    electronApp = await electron.launch({
      args: [APP_PATH, "--no-sandbox"],
      env: { ...process.env, DISPLAY: process.env.DISPLAY || ":1" },
    });
    window = await electronApp.firstWindow();
    await window.waitForLoadState("domcontentloaded");
    await window.waitForTimeout(1500);
  });

  test.afterAll(async () => {
    if (electronApp) {
      await electronApp.close();
    }
    if (fs.existsSync(DATA_JS_BACKUP)) {
      fs.renameSync(DATA_JS_BACKUP, DATA_JS);
    }
  });

  test("should show setup screen when data.js is missing", async () => {
    const setupScreen = window.locator("#setup-screen");
    const display = await setupScreen.evaluate((el) => getComputedStyle(el).display);
    expect(display).not.toBe("none");
  });

  test("should display welcome title", async () => {
    const title = window.locator(".setup-title");
    await expect(title).toContainText("Welcome to ClawRecord");
  });

  test("should display welcome description", async () => {
    const desc = window.locator(".setup-desc");
    await expect(desc).toContainText("OpenClaw dashboard");
  });

  test("should display environment status items", async () => {
    const statusItems = window.locator(".setup-status-item");
    const count = await statusItems.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test("should detect Python availability in setup", async () => {
    const content = await window.locator("#setup-status").innerHTML();
    expect(content).toContain("Python 3");
  });

  test("should show action buttons", async () => {
    const actions = window.locator("#setup-actions");
    const display = await actions.evaluate((el) => getComputedStyle(el).display);
    expect(display).not.toBe("none");
  });

  test("should have Auto Setup button", async () => {
    const autoBtn = window.locator(".setup-btn.primary");
    await expect(autoBtn).toBeVisible();
    const text = await autoBtn.textContent();
    expect(text).toContain("Auto Setup");
  });

  test("should have Skip Setup option", async () => {
    const skipBtn = window.locator(".setup-btn.ghost");
    await expect(skipBtn).toBeVisible();
  });

  test("should display language switcher in setup", async () => {
    const langSw = window.locator(".setup-lang");
    await expect(langSw).toBeVisible();
  });

  test("should switch setup screen to Chinese", async () => {
    const zhBtn = window.locator(".setup-lang button:nth-child(2)");
    await zhBtn.click();
    await window.waitForTimeout(500);

    const title = window.locator(".setup-title");
    await expect(title).toContainText("欢迎使用 ClawRecord");
  });

  test("should switch setup screen back to English", async () => {
    const enBtn = window.locator(".setup-lang button:first-child");
    await enBtn.click();
    await window.waitForTimeout(500);

    const title = window.locator(".setup-title");
    await expect(title).toContainText("Welcome to ClawRecord");
  });

  test("should hide setup and show dashboard on Skip", async () => {
    const skipBtn = window.locator(".setup-btn.ghost");
    await skipBtn.click();
    await window.waitForTimeout(500);

    const setupScreen = window.locator("#setup-screen");
    const setupDisplay = await setupScreen.evaluate((el) => getComputedStyle(el).display);
    expect(setupDisplay).toBe("none");

    const app = window.locator("#app");
    const appDisplay = await app.evaluate((el) => getComputedStyle(el).display);
    expect(appDisplay).not.toBe("none");
  });
});

test.describe("Setup Screen (with data)", () => {
  let electronApp2;
  let window2;

  test.beforeAll(async () => {
    const dataExists = fs.existsSync(DATA_JS);
    if (!dataExists && fs.existsSync(DATA_JS_BACKUP)) {
      fs.renameSync(DATA_JS_BACKUP, DATA_JS);
    }

    electronApp2 = await electron.launch({
      args: [APP_PATH, "--no-sandbox"],
      env: { ...process.env, DISPLAY: process.env.DISPLAY || ":1" },
    });
    window2 = await electronApp2.firstWindow();
    await window2.waitForLoadState("domcontentloaded");
    await window2.waitForTimeout(1500);
  });

  test.afterAll(async () => {
    if (electronApp2) {
      await electronApp2.close();
    }
  });

  test("should NOT show setup screen when data.js exists", async () => {
    const setupScreen = window2.locator("#setup-screen");
    const display = await setupScreen.evaluate((el) => getComputedStyle(el).display);
    expect(display).toBe("none");
  });

  test("should show dashboard directly", async () => {
    const app = window2.locator("#app");
    const display = await app.evaluate((el) => getComputedStyle(el).display);
    expect(display).not.toBe("none");

    const content = await app.innerHTML();
    expect(content.length).toBeGreaterThan(100);
  });
});
