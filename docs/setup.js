/* ═══════════════════════════════════════════
   ClawRecord Desktop — Setup & Auto-Install
   ═══════════════════════════════════════════ */
(function () {
  "use strict";

  const isElectron = typeof window.clawrecord !== "undefined";
  if (!isElectron) return;

  let lang = localStorage.getItem("cr-lang") || "en";

  const i18n = {
    en: {
      welcome_title: "Welcome to ClawRecord",
      welcome_desc: "Your personal gamified OpenClaw dashboard",
      checking: "Checking environment...",
      openclaw_found: "OpenClaw detected",
      openclaw_not_found: "OpenClaw not detected",
      python_found: "Python 3 available",
      python_not_found: "Python 3 not available",
      hook_installed: "ClawRecord hook installed",
      hook_not_installed: "ClawRecord hook not installed",
      data_ready: "Dashboard data ready",
      data_not_ready: "Dashboard data needs to be generated",
      auto_setup: "Auto Setup",
      auto_setup_desc:
        "Automatically install OpenClaw and configure ClawRecord",
      install_openclaw: "Install OpenClaw",
      install_openclaw_desc: "Install OpenClaw globally via npm",
      install_hook: "Install Hook",
      install_hook_desc: "Install the ClawRecord tracking hook",
      generate_data: "Generate Data",
      generate_data_desc: "Collect data and generate dashboard",
      skip: "Skip Setup",
      skip_desc: "I already have OpenClaw set up",
      installing: "Installing...",
      install_success: "Installation complete!",
      install_failed: "Installation failed",
      all_done: "All set! Loading dashboard...",
      step_install_openclaw: "Installing OpenClaw...",
      step_install_hook: "Installing ClawRecord hook...",
      step_generate: "Generating dashboard data...",
      refreshing: "Refreshing data...",
      refresh_done: "Data refreshed!",
      refresh_fail: "Refresh failed",
      manual_install_title: "Manual Installation",
      manual_install_desc:
        'Run these commands in your terminal to install OpenClaw:',
      manual_cmd_npm: "npm install -g openclaw",
      open_dir: "Open OpenClaw Directory",
      version_info: "App Info",
    },
    zh: {
      welcome_title: "欢迎使用 ClawRecord",
      welcome_desc: "你的个人游戏化 OpenClaw 仪表盘",
      checking: "检测环境...",
      openclaw_found: "已检测到 OpenClaw",
      openclaw_not_found: "未检测到 OpenClaw",
      python_found: "Python 3 可用",
      python_not_found: "Python 3 不可用",
      hook_installed: "ClawRecord hook 已安装",
      hook_not_installed: "ClawRecord hook 未安装",
      data_ready: "仪表盘数据已就绪",
      data_not_ready: "仪表盘数据需要生成",
      auto_setup: "一键安装",
      auto_setup_desc: "自动安装 OpenClaw 并配置 ClawRecord",
      install_openclaw: "安装 OpenClaw",
      install_openclaw_desc: "通过 npm 全局安装 OpenClaw",
      install_hook: "安装 Hook",
      install_hook_desc: "安装 ClawRecord 数据追踪钩子",
      generate_data: "生成数据",
      generate_data_desc: "采集数据并生成仪表盘",
      skip: "跳过设置",
      skip_desc: "我已经配置好了 OpenClaw",
      installing: "安装中...",
      install_success: "安装完成！",
      install_failed: "安装失败",
      all_done: "设置完成！正在加载仪表盘...",
      step_install_openclaw: "正在安装 OpenClaw...",
      step_install_hook: "正在安装 ClawRecord hook...",
      step_generate: "正在生成仪表盘数据...",
      refreshing: "正在刷新数据...",
      refresh_done: "数据已刷新！",
      refresh_fail: "刷新失败",
      manual_install_title: "手动安装",
      manual_install_desc: "在终端中运行以下命令安装 OpenClaw：",
      manual_cmd_npm: "npm install -g openclaw",
      open_dir: "打开 OpenClaw 目录",
      version_info: "应用信息",
    },
  };

  const L = () => i18n[lang] || i18n.en;
  const h = (s) =>
    String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  window._setupModule = {
    showSetup,
    hideSetup,
    isElectron: true,
  };

  async function showSetup() {
    const screen = document.getElementById("setup-screen");
    const app = document.getElementById("app");
    const tabs = document.getElementById("tabs");
    const sidebar = document.getElementById("sidebar");
    screen.style.display = "block";
    app.style.display = "none";
    tabs.style.display = "none";
    if (sidebar) sidebar.style.display = "none";

    const l = L();
    screen.innerHTML = `
<div class="setup-container">
  <div class="setup-header">
    <div class="setup-logo">🐾</div>
    <h1 class="setup-title">${h(l.welcome_title)}</h1>
    <p class="setup-desc">${h(l.welcome_desc)}</p>
    <div class="setup-lang">
      <button class="${lang === "en" ? "active" : ""}" onclick="window._setupSetLang('en')">EN</button>
      <button class="${lang === "zh" ? "active" : ""}" onclick="window._setupSetLang('zh')">ZH</button>
    </div>
  </div>
  <div class="setup-status" id="setup-status">
    <div class="setup-status-item" id="ss-checking">
      <span class="setup-spinner"></span>
      <span>${h(l.checking)}</span>
    </div>
  </div>
  <div class="setup-actions" id="setup-actions" style="display:none"></div>
  <div class="setup-log" id="setup-log" style="display:none">
    <pre id="setup-log-content"></pre>
  </div>
</div>`;

    await checkEnvironment();
  }

  window._setupSetLang = function (newLang) {
    lang = newLang;
    localStorage.setItem("cr-lang", lang);
    showSetup();
  };

  async function checkEnvironment() {
    const l = L();
    try {
      const status = await window.clawrecord.checkOpenClaw();
      const dataExists = await window.clawrecord.checkDataExists();

      const statusEl = document.getElementById("setup-status");
      const actionsEl = document.getElementById("setup-actions");

      const items = [
        {
          ok: !!status.binary,
          yes: l.openclaw_found,
          no: l.openclaw_not_found,
          detail: status.binary || "",
        },
        {
          ok: status.pythonAvailable,
          yes: l.python_found,
          no: l.python_not_found,
        },
        {
          ok: status.installed,
          yes: l.hook_installed,
          no: l.hook_not_installed,
          detail: status.path,
        },
        { ok: dataExists, yes: l.data_ready, no: l.data_not_ready },
      ];

      statusEl.innerHTML = items
        .map(
          (it) => `
        <div class="setup-status-item ${it.ok ? "ok" : "warn"}">
          <span class="setup-icon">${it.ok ? "✅" : "⚠️"}</span>
          <span>${h(it.ok ? it.yes : it.no)}</span>
          ${it.detail ? `<span class="setup-detail">${h(it.detail)}</span>` : ""}
        </div>`
        )
        .join("");

      const allOk = items.every((i) => i.ok);
      actionsEl.style.display = "flex";

      if (allOk) {
        actionsEl.innerHTML = `
          <button class="setup-btn primary" onclick="window._setupDone()">
            🚀 ${h(l.all_done.replace("...", ""))}
          </button>
          <button class="setup-btn secondary" onclick="window._setupRefresh()">
            🔄 ${h(l.generate_data)}
          </button>`;
        setTimeout(() => window._setupDone(), 1500);
      } else {
        actionsEl.innerHTML = `
          <button class="setup-btn primary" onclick="window._setupAutoInstall()">
            ⚡ ${h(l.auto_setup)}
            <span class="setup-btn-desc">${h(l.auto_setup_desc)}</span>
          </button>
          ${
            !status.binary
              ? `<button class="setup-btn secondary" onclick="window._setupManual()">
              📋 ${h(l.manual_install_title)}
            </button>`
              : ""
          }
          <button class="setup-btn ghost" onclick="window._setupDone()">
            ${h(l.skip)} →
          </button>`;
      }
    } catch (err) {
      document.getElementById("setup-status").innerHTML = `
        <div class="setup-status-item warn">
          <span class="setup-icon">❌</span>
          <span>${h(err.message)}</span>
        </div>`;
      document.getElementById("setup-actions").style.display = "flex";
      document.getElementById("setup-actions").innerHTML = `
        <button class="setup-btn ghost" onclick="window._setupDone()">
          ${h(L().skip)} →
        </button>`;
    }
  }

  window._setupAutoInstall = async function () {
    const l = L();
    const actionsEl = document.getElementById("setup-actions");
    const logEl = document.getElementById("setup-log");
    const logContent = document.getElementById("setup-log-content");
    actionsEl.style.display = "none";
    logEl.style.display = "block";
    logContent.textContent = "";

    const addLog = (msg) => {
      logContent.textContent += msg + "\n";
      logContent.scrollTop = logContent.scrollHeight;
    };

    const unsubProgress = window.clawrecord.onInstallProgress((data) => {
      addLog(data.data.trim());
    });

    const unsubStep = window.clawrecord.onSetupStep((data) => {
      const statusMap = {
        running: "⏳",
        done: "✅",
        error: "❌",
        skipped: "⏭️",
      };
      addLog(
        `${statusMap[data.status] || "•"} ${data.step} — ${data.status}${data.message ? ": " + data.message : ""}${data.error ? ": " + data.error : ""}`
      );
    });

    try {
      addLog(`⚡ ${l.auto_setup}...\n`);
      const result = await window.clawrecord.setupOpenClaw();

      if (result.success) {
        addLog(`\n📊 ${l.step_generate}`);
        const refreshResult = await window.clawrecord.refreshData();
        if (refreshResult.success) {
          addLog(`✅ ${l.install_success}`);
        } else {
          addLog(`⚠️ ${l.refresh_fail}: ${refreshResult.error || ""}`);
        }
      } else {
        addLog(`\n❌ ${l.install_failed}: ${result.error || ""}`);
      }
    } catch (err) {
      addLog(`\n❌ ${err.message}`);
    }

    unsubProgress();
    unsubStep();

    actionsEl.style.display = "flex";
    actionsEl.innerHTML = `
      <button class="setup-btn primary" onclick="window._setupDone()">
        🚀 ${h(l.all_done.replace("...", ""))}
      </button>
      <button class="setup-btn secondary" onclick="window._setupAutoInstall()">
        🔄 ${h(l.auto_setup)}
      </button>`;
  };

  window._setupRefresh = async function () {
    const l = L();
    const actionsEl = document.getElementById("setup-actions");
    actionsEl.innerHTML = `<div class="setup-spinner-large"></div><p>${h(l.refreshing)}</p>`;

    try {
      const result = await window.clawrecord.refreshData();
      if (result.success) {
        actionsEl.innerHTML = `<p>✅ ${h(l.refresh_done)}</p>`;
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        actionsEl.innerHTML = `<p>❌ ${h(l.refresh_fail)}: ${h(result.error || "")}</p>
          <button class="setup-btn ghost" onclick="window._setupDone()">
            ${h(l.skip)} →
          </button>`;
      }
    } catch (err) {
      actionsEl.innerHTML = `<p>❌ ${h(err.message)}</p>`;
    }
  };

  window._setupManual = function () {
    const l = L();
    const actionsEl = document.getElementById("setup-actions");
    actionsEl.innerHTML = `
      <div class="setup-manual">
        <h3>${h(l.manual_install_title)}</h3>
        <p>${h(l.manual_install_desc)}</p>
        <code class="setup-code">${h(l.manual_cmd_npm)}</code>
      </div>
      <button class="setup-btn secondary" onclick="window._setupRecheck()">
        🔄 Re-check
      </button>
      <button class="setup-btn ghost" onclick="window._setupDone()">
        ${h(l.skip)} →
      </button>`;
  };

  window._setupRecheck = function () {
    showSetup();
  };

  window._setupDone = function () {
    hideSetup();
  };

  function hideSetup() {
    const screen = document.getElementById("setup-screen");
    const app = document.getElementById("app");
    const tabs = document.getElementById("tabs");
    const sidebar = document.getElementById("sidebar");
    screen.style.display = "none";
    app.style.display = "";
    tabs.style.display = "";
    if (sidebar) sidebar.style.display = "";
  }

  if (isElectron && window.clawrecord.onTriggerRefresh) {
    window.clawrecord.onTriggerRefresh(async () => {
      const result = await window.clawrecord.refreshData();
      if (result.success) {
        window.location.reload();
      }
    });
  }
})();
