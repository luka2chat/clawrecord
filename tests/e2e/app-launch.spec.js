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
});

test.afterAll(async () => {
  if (electronApp) {
    await electronApp.close();
  }
});

test.describe("App Launch", () => {
  test("should create a main window", async () => {
    const windows = electronApp.windows();
    expect(windows.length).toBeGreaterThanOrEqual(1);
  });

  test("should have correct window title", async () => {
    const title = await window.title();
    expect(title).toBe("ClawRecord");
  });

  test("should load index.html from docs/", async () => {
    const url = window.url();
    expect(url).toContain("docs/index.html");
  });

  test("should have a visible app container", async () => {
    const app = window.locator("#app");
    await expect(app).toBeAttached();
  });

  test("should have navigation tabs", async () => {
    const tabs = window.locator("#tabs");
    await expect(tabs).toBeAttached();

    const tabButtons = window.locator("#tabs .tab");
    const count = await tabButtons.count();
    expect(count).toBe(5);
  });

  test("should have sidebar navigation on desktop", async () => {
    const sidebar = window.locator("#sidebar");
    await expect(sidebar).toBeVisible();

    const sidebarItems = window.locator("#sidebar .sb-item");
    const count = await sidebarItems.count();
    expect(count).toBe(5);
  });

  test("should expose clawrecord API via preload", async () => {
    const hasApi = await window.evaluate(() => {
      return typeof window.clawrecord !== "undefined";
    });
    expect(hasApi).toBe(true);
  });

  test("should expose all expected API methods", async () => {
    const methods = await window.evaluate(() => {
      const api = window.clawrecord;
      return {
        checkOpenClaw: typeof api.checkOpenClaw,
        installOpenClaw: typeof api.installOpenClaw,
        installHook: typeof api.installHook,
        setupOpenClaw: typeof api.setupOpenClaw,
        refreshData: typeof api.refreshData,
        runScript: typeof api.runScript,
        getAppInfo: typeof api.getAppInfo,
        openExternal: typeof api.openExternal,
        openPath: typeof api.openPath,
        checkDataExists: typeof api.checkDataExists,
        onInstallProgress: typeof api.onInstallProgress,
        onSetupStep: typeof api.onSetupStep,
        onTriggerRefresh: typeof api.onTriggerRefresh,
      };
    });

    for (const [name, type] of Object.entries(methods)) {
      expect(type, `API method '${name}' should be a function`).toBe("function");
    }
  });

  test("should have correct minimum window size", async () => {
    const size = await window.evaluate(() => {
      return {
        width: window.outerWidth,
        height: window.outerHeight,
      };
    });
    expect(size.width).toBeGreaterThanOrEqual(380);
    expect(size.height).toBeGreaterThanOrEqual(600);
  });
});
