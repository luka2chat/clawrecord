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

test.describe("IPC: check-openclaw", () => {
  test("should return environment status object", async () => {
    const result = await window.evaluate(() => window.clawrecord.checkOpenClaw());

    expect(result).toHaveProperty("installed");
    expect(result).toHaveProperty("hasConfig");
    expect(result).toHaveProperty("hasSessions");
    expect(result).toHaveProperty("path");
    expect(result).toHaveProperty("pythonAvailable");

    expect(typeof result.installed).toBe("boolean");
    expect(typeof result.hasConfig).toBe("boolean");
    expect(typeof result.hasSessions).toBe("boolean");
    expect(typeof result.path).toBe("string");
    expect(typeof result.pythonAvailable).toBe("boolean");
  });

  test("should detect Python 3 availability", async () => {
    const result = await window.evaluate(() => window.clawrecord.checkOpenClaw());
    expect(result.pythonAvailable).toBe(true);
  });

  test("should return a valid path for OpenClaw directory", async () => {
    const result = await window.evaluate(() => window.clawrecord.checkOpenClaw());
    expect(result.path).toContain(".openclaw");
  });
});

test.describe("IPC: get-app-info", () => {
  test("should return app information", async () => {
    const info = await window.evaluate(() => window.clawrecord.getAppInfo());

    expect(info).toHaveProperty("version");
    expect(info).toHaveProperty("platform");
    expect(info).toHaveProperty("arch");
    expect(info).toHaveProperty("electronVersion");
    expect(info).toHaveProperty("nodeVersion");
    expect(info).toHaveProperty("openClawDir");
    expect(info).toHaveProperty("resourcePath");
  });

  test("should have valid version string", async () => {
    const info = await window.evaluate(() => window.clawrecord.getAppInfo());
    expect(info.version).toMatch(/^\d+\.\d+\.\d+/);
  });

  test("should report correct platform", async () => {
    const info = await window.evaluate(() => window.clawrecord.getAppInfo());
    expect(["linux", "darwin", "win32"]).toContain(info.platform);
  });

  test("should have electron version", async () => {
    const info = await window.evaluate(() => window.clawrecord.getAppInfo());
    expect(info.electronVersion).toBeTruthy();
    expect(info.electronVersion.length).toBeGreaterThan(0);
  });
});

test.describe("IPC: check-data-exists", () => {
  test("should return boolean for data.js existence", async () => {
    const exists = await window.evaluate(() => window.clawrecord.checkDataExists());
    expect(typeof exists).toBe("boolean");
  });

  test("should return consistent result for data.js check", async () => {
    const exists = await window.evaluate(() => window.clawrecord.checkDataExists());
    expect(typeof exists).toBe("boolean");
  });
});

test.describe("IPC: run-script", () => {
  test("should fail gracefully for non-existent script", async () => {
    const result = await window.evaluate(() =>
      window.clawrecord.runScript("nonexistent.py")
    );
    expect(result.success).toBe(false);
    expect(result.error).toContain("not found");
  });
});

test.describe("IPC: install-hook", () => {
  test("should install hook and return result", async () => {
    const result = await window.evaluate(() => window.clawrecord.installHook());
    expect(result).toHaveProperty("success");
    expect(result.success).toBe(true);
    expect(result).toHaveProperty("path");
  });
});
