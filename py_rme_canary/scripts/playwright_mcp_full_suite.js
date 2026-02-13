#!/usr/bin/env node
/*
 * Playwright MCP full-suite exerciser.
 *
 * Runs broad functional coverage over available MCP tools and writes a
 * detailed machine-readable report.
 *
 * Usage:
 *   node py_rme_canary/scripts/playwright_mcp_full_suite.js
 *
 * Env vars:
 *   PLAYWRIGHT_MCP_URL=http://localhost:8931/mcp
 *   PLAYWRIGHT_MCP_FULL_REPORT=.quality_reports/playwright_mcp_full_suite_report.json
 *   PLAYWRIGHT_MCP_FULL_ARTIFACTS=.quality_reports/playwright_mcp_full_suite
 */

const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

const localRequire = createRequire(__filename);
const mcpRequire = (() => {
  try {
    localRequire.resolve("@modelcontextprotocol/sdk/client/index.js");
    return localRequire;
  } catch {
    return createRequire("/home/marcelo/.local/playwright-mcp/package.json");
  }
})();

const { Client } = mcpRequire("@modelcontextprotocol/sdk/client/index.js");
const { StreamableHTTPClientTransport } = mcpRequire("@modelcontextprotocol/sdk/client/streamableHttp.js");

const mcpUrl = process.env.PLAYWRIGHT_MCP_URL || "http://localhost:8931/mcp";
const reportPath = process.env.PLAYWRIGHT_MCP_FULL_REPORT || ".quality_reports/playwright_mcp_full_suite_report.json";
const artifactsDirRaw = process.env.PLAYWRIGHT_MCP_FULL_ARTIFACTS || ".quality_reports/playwright_mcp_full_suite";

function ensureDir(targetDir) {
  const resolved = path.resolve(targetDir);
  fs.mkdirSync(resolved, { recursive: true });
  return resolved;
}

function ensureFileDir(targetFile) {
  const resolved = path.resolve(targetFile);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  return resolved;
}

function toolText(response) {
  const content = response?.content || [];
  return content.filter((entry) => entry?.type === "text").map((entry) => entry?.text || "").join("\n");
}

function shorten(text, max = 5000) {
  const raw = String(text || "");
  return raw.length <= max ? raw : `${raw.slice(0, max)}\n...[truncated]`;
}

function extractRef(snapshotText, matcher) {
  const lines = String(snapshotText || "").split("\n");
  for (const line of lines) {
    if (!matcher.test(line)) {
      continue;
    }
    const refMatch = line.match(/\[ref=(e\d+)\]/);
    if (refMatch) {
      return refMatch[1];
    }
  }
  return null;
}

function parseResultJson(text) {
  const raw = String(text || "");
  const marker = "### Result";
  const markerIdx = raw.indexOf(marker);
  if (markerIdx < 0) {
    return null;
  }

  const tail = raw.slice(markerIdx + marker.length).trim();
  const fenced = tail.match(/^```json\s*([\s\S]*?)\s*```/i);
  if (fenced) {
    try {
      return JSON.parse(fenced[1]);
    } catch {
      return null;
    }
  }

  const section = tail.split(/\n###\s+/)[0].trim();
  if (!section.startsWith("{") && !section.startsWith("[")) {
    return null;
  }
  try {
    return JSON.parse(section);
  } catch {
    return null;
  }
}

function buildPlaygroundDataUrl() {
  const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>MCP Playground</title>
  <style>
    body { font-family: sans-serif; padding: 16px; }
    #hoverBox, #dragSrc, #dropDst { padding: 8px; border: 1px solid #999; margin: 8px 0; }
    #dropDst { min-height: 28px; }
  </style>
</head>
<body>
  <h1>MCP Playground</h1>
  <label for="name">Name Field</label>
  <input id="name" placeholder="Type name" />
  <label for="mode">Mode</label>
  <select id="mode">
    <option value="alpha">Alpha</option>
    <option value="beta">Beta</option>
  </select>
  <button id="confirmBtn" onclick="document.getElementById('result').textContent=(confirm('Proceed with action?') ? 'confirm-accepted' : 'confirm-dismissed')">Open Confirm</button>
  <button id="tabBtn" onclick="window.open('https://example.com','_blank');document.getElementById('result').textContent='tab-opened'">Open Tab</button>
  <div id="hoverBox" tabindex="0">Hover Target</div>
  <div id="dragSrc" draggable="true">Drag Source</div>
  <div id="dropDst">Drop Target</div>
  <input id="fileInput" type="file" />
  <button id="submitBtn" onclick="document.getElementById('result').textContent='submitted:'+document.getElementById('name').value">Submit Form</button>
  <a id="navLink" href="https://example.com/?from=playground">Visit Example</a>
  <pre id="result">ready</pre>
  <script>
    const src = document.getElementById('dragSrc');
    const dst = document.getElementById('dropDst');
    src.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', 'dragged');
    });
    dst.addEventListener('dragover', (e) => e.preventDefault());
    dst.addEventListener('drop', (e) => {
      e.preventDefault();
      document.getElementById('result').textContent = 'dropped';
    });
  </script>
</body>
</html>`;

  return `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
}

async function run() {
  const reportFile = ensureFileDir(reportPath);
  const artifactsDir = ensureDir(artifactsDirRaw);
  const uploadSampleFile = path.join(artifactsDir, "upload_sample.txt");
  fs.writeFileSync(uploadSampleFile, "playwright mcp upload sample\n", "utf-8");

  const report = {
    ok: false,
    startedAt: new Date().toISOString(),
    mcpUrl,
    artifactsDir,
    uploadSampleFile,
    toolsAvailable: [],
    toolsCalled: [],
    toolsMissingCoverage: [],
    failedSteps: [],
    steps: [],
    refs: {},
  };

  const calledTools = new Set();

    const client = new Client({ name: "playwright-mcp-full-suite", version: "1.0.0" }, { capabilities: {} });
    const transport = new StreamableHTTPClientTransport(new URL(mcpUrl));

  async function step(stepName, toolName, argsBuilder) {
    const entry = {
      step: stepName,
      tool: toolName,
      status: "skipped",
      startedAt: new Date().toISOString(),
    };

    try {
      if (!report.toolsAvailable.includes(toolName)) {
        entry.status = "skipped";
        entry.reason = "tool_not_available";
        return entry;
      }

      const args = typeof argsBuilder === "function" ? argsBuilder() : (argsBuilder || {});
      if (args === null) {
        entry.status = "skipped";
        entry.reason = "prerequisite_not_met";
        return entry;
      }

      const response = await client.callTool({ name: toolName, arguments: args });
      calledTools.add(toolName);

      entry.status = response?.isError ? "failed" : "passed";
      entry.arguments = args;
      entry.text = shorten(toolText(response));
      entry.isError = !!response?.isError;
    } catch (error) {
      entry.status = "error";
      entry.error = String(error?.stack || error);
    } finally {
      entry.finishedAt = new Date().toISOString();
      report.steps.push(entry);
      return entry;
    }
  }

  function validationStep(stepName, passed, details) {
    report.steps.push({
      step: stepName,
      tool: "validation",
      status: passed ? "passed" : "failed",
      details,
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
    });
  }

  try {
    await client.connect(transport);

    const toolsResp = await client.listTools();
    const tools = toolsResp?.tools || [];
    report.toolsAvailable = tools.map((tool) => tool.name);
    report.toolsSchemas = Object.fromEntries(
      tools.map((tool) => [tool.name, tool.inputSchema || {}]),
    );

    const installStep = await step("install_browser_runtime", "browser_install", {});
    if (
      installStep.status === "failed"
      && /running 'npx playwright install'/i.test(String(installStep.text || ""))
    ) {
      installStep.status = "passed";
      installStep.toleratedWarning = "browser_install returned non-fatal install warning";
    }

    await step("tabs_list_initial", "browser_tabs", { action: "list" });
    await step("tabs_new", "browser_tabs", { action: "new" });
    await step("tabs_list_after_new", "browser_tabs", { action: "list" });
    await step("tabs_select_zero", "browser_tabs", { action: "select", index: 0 });
    await step("tabs_close_index_one", "browser_tabs", { action: "close", index: 1 });

    await step("navigate_playground", "browser_navigate", { url: buildPlaygroundDataUrl() });
    await step("resize_viewport", "browser_resize", { width: 1366, height: 768 });

    const snapshotStep = await step("snapshot_playground", "browser_snapshot", {});
    const snapshotFile = path.join(artifactsDir, "playground_snapshot.md");
    if (snapshotStep.status === "passed") {
      fs.writeFileSync(snapshotFile, String(snapshotStep.text || ""), "utf-8");
    }
    await step("snapshot_playground_file", "browser_snapshot", {
      filename: path.basename(snapshotFile),
    });

    const snapshotText = snapshotStep.text || "";
    report.refs.nameInput = extractRef(snapshotText, /textbox "Name Field"/);
    report.refs.modeCombobox = extractRef(snapshotText, /combobox "Mode"/);
    report.refs.confirmButton = extractRef(snapshotText, /button "Open Confirm"/);
    report.refs.tabButton = extractRef(snapshotText, /button "Open Tab"/);
    report.refs.hoverTarget = extractRef(snapshotText, /Hover Target/);
    report.refs.dragSource = extractRef(snapshotText, /Drag Source/);
    report.refs.dropTarget = extractRef(snapshotText, /Drop Target/);
    report.refs.chooseFileButton = extractRef(snapshotText, /button "Choose File"/);
    report.refs.submitButton = extractRef(snapshotText, /button "Submit Form"/);
    report.refs.visitExampleLink = extractRef(snapshotText, /link "Visit Example"/);

    await step("fill_form", "browser_fill_form", () => {
      if (!report.refs.nameInput || !report.refs.modeCombobox) {
        return null;
      }
      return {
        fields: [
          { name: "Name Field", type: "textbox", ref: report.refs.nameInput, value: "Noct" },
          { name: "Mode", type: "combobox", ref: report.refs.modeCombobox, value: "Beta" },
        ],
      };
    });

    await step("type_name_suffix", "browser_type", () => {
      if (!report.refs.nameInput) {
        return null;
      }
      return { ref: report.refs.nameInput, text: " Map Editor", slowly: false };
    });

    await step("press_key_enter", "browser_press_key", { key: "Enter" });

    await step("select_option_alpha", "browser_select_option", () => {
      if (!report.refs.modeCombobox) {
        return null;
      }
      return { element: "Mode", ref: report.refs.modeCombobox, values: ["alpha"] };
    });

    await step("hover_target", "browser_hover", () => {
      if (!report.refs.hoverTarget) {
        return null;
      }
      return { element: "Hover Target", ref: report.refs.hoverTarget };
    });

    await step("drag_source_to_target", "browser_drag", () => {
      if (!report.refs.dragSource || !report.refs.dropTarget) {
        return null;
      }
      return {
        startElement: "Drag Source",
        startRef: report.refs.dragSource,
        endElement: "Drop Target",
        endRef: report.refs.dropTarget,
      };
    });
    await step("wait_for_drag_result", "browser_wait_for", { text: "dropped" });

    await step("open_confirm_dialog_dismiss", "browser_click", () => {
      if (!report.refs.confirmButton) {
        return null;
      }
      return { element: "Open Confirm", ref: report.refs.confirmButton };
    });
    await step("handle_confirm_dialog_dismiss", "browser_handle_dialog", { accept: false });
    await step("wait_for_confirm_dismiss", "browser_wait_for", { text: "confirm-dismissed" });
    await step("open_confirm_dialog_accept", "browser_click", () => {
      if (!report.refs.confirmButton) {
        return null;
      }
      return { element: "Open Confirm", ref: report.refs.confirmButton };
    });
    await step("handle_confirm_dialog_accept", "browser_handle_dialog", { accept: true });
    await step("wait_for_confirm_accept", "browser_wait_for", { text: "confirm-accepted" });

    await step("open_new_tab_from_button", "browser_click", () => {
      if (!report.refs.tabButton) {
        return null;
      }
      return { element: "Open Tab", ref: report.refs.tabButton };
    });
    await step("tabs_list_after_button", "browser_tabs", { action: "list" });
    await step("tabs_select_new_tab", "browser_tabs", { action: "select", index: 1 });
    await step("wait_for_example_domain_tab", "browser_wait_for", { text: "Example Domain" });
    await step("tabs_close_new_tab", "browser_tabs", { action: "close", index: 1 });
    await step("tabs_select_main_after_close", "browser_tabs", { action: "select", index: 0 });
    await step("wait_for_playground_after_tab_close", "browser_wait_for", { text: "MCP Playground" });

    await step("open_file_chooser", "browser_click", () => {
      if (!report.refs.chooseFileButton) {
        return null;
      }
      return { element: "Choose File", ref: report.refs.chooseFileButton };
    });

    await step("file_upload", "browser_file_upload", { paths: [uploadSampleFile] });
    const uploadState = await step("evaluate_uploaded_file_state", "browser_evaluate", {
      function: "() => { const fi = document.getElementById('fileInput'); const f = fi && fi.files && fi.files[0] ? fi.files[0] : null; return { count: fi && fi.files ? fi.files.length : 0, name: f ? f.name : '', size: f ? f.size : 0 }; }",
    });
    const uploadStateObj = parseResultJson(uploadState.text);
    validationStep(
      "validate_uploaded_file_state",
      !!uploadStateObj
        && Number(uploadStateObj.count) === 1
        && String(uploadStateObj.name || "") === "upload_sample.txt"
        && Number(uploadStateObj.size || 0) > 0,
      uploadStateObj,
    );

    await step("click_submit", "browser_click", () => {
      if (!report.refs.submitButton) {
        return null;
      }
      return { element: "Submit Form", ref: report.refs.submitButton };
    });

    await step("run_code_async_result", "browser_run_code", {
      code: "async (page) => { await page.evaluate(() => { setTimeout(() => { document.getElementById('result').textContent = 'async-ready'; }, 300); }); }",
    });

    await step("wait_for_async_result", "browser_wait_for", { text: "async-ready" });

    await step("run_code_temp_marker", "browser_run_code", {
      code: "async (page) => { await page.evaluate(() => { document.getElementById('result').textContent = 'temp-marker'; setTimeout(() => { document.getElementById('result').textContent = 'temp-cleared'; }, 300); }); }",
    });

    await step("wait_for_text_gone", "browser_wait_for", { textGone: "temp-marker" });
    await step("wait_for_small_time", "browser_wait_for", { time: 0.2 });

    await step("evaluate_result_payload", "browser_evaluate", {
      function: "() => ({ title: document.title, result: document.getElementById('result')?.textContent, mode: document.getElementById('mode')?.value })",
    });
    const resultPayloadStep = report.steps.find((entry) => entry.step === "evaluate_result_payload");
    const resultPayload = parseResultJson(resultPayloadStep?.text);
    validationStep(
      "validate_result_payload",
      !!resultPayload
        && String(resultPayload.title || "") === "MCP Playground"
        && String(resultPayload.result || "") === "temp-cleared"
        && String(resultPayload.mode || "") === "alpha",
      resultPayload,
    );

    await step("click_visit_example_link", "browser_click", () => {
      if (!report.refs.visitExampleLink) {
        return null;
      }
      return { element: "Visit Example", ref: report.refs.visitExampleLink };
    });

    await step("wait_for_example_domain", "browser_wait_for", { text: "Example Domain" });
    await step("navigate_back", "browser_navigate_back", {});
    await step("wait_for_playground_title", "browser_wait_for", { text: "MCP Playground" });

    const networkFile = path.join(artifactsDir, "network_requests.log");
    await step("network_requests_dump", "browser_network_requests", {
      includeStatic: false,
      filename: path.basename(networkFile),
    });

    await step("run_code_console_messages", "browser_run_code", {
      code: "async (page) => { await page.evaluate(() => { console.debug('mcp-debug-message'); console.warn('mcp-warning-message'); console.error('mcp-error-message'); }); }",
    });

    const consoleFile = path.join(artifactsDir, "console_messages.log");
    await step("console_messages_dump", "browser_console_messages", {
      level: "debug",
      filename: path.basename(consoleFile),
    });
    await step("console_messages_dump_errors", "browser_console_messages", {
      level: "error",
    });

    const viewportShot = path.join(artifactsDir, "playground_viewport.png");
    await step("screenshot_viewport", "browser_take_screenshot", {
      type: "png",
      filename: path.basename(viewportShot),
      fullPage: false,
    });

    const fullShot = path.join(artifactsDir, "playground_fullpage.png");
    await step("screenshot_fullpage", "browser_take_screenshot", {
      type: "png",
      filename: path.basename(fullShot),
      fullPage: true,
    });

    await step("tabs_list_final", "browser_tabs", { action: "list" });
    await step("close_current_page", "browser_close", {});

    report.toolsCalled = Array.from(calledTools).sort();

    const available = new Set(report.toolsAvailable);
    const called = new Set(report.toolsCalled);
    report.toolsMissingCoverage = Array.from(available).filter((name) => !called.has(name)).sort();

    const failedSteps = report.steps.filter((stepEntry) => ["failed", "error"].includes(stepEntry.status));
    report.failedSteps = failedSteps.map((s) => ({ step: s.step, tool: s.tool, status: s.status }));

    report.ok = failedSteps.length === 0;
  } catch (error) {
    report.ok = false;
    report.error = String(error?.stack || error);
  } finally {
    try {
      await client.close();
    } catch {
      // ignore
    }

    report.finishedAt = new Date().toISOString();
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2), "utf-8");

    const output = {
      ok: report.ok,
      mcpUrl,
      reportPath: reportFile,
      artifactsDir,
      toolsAvailable: report.toolsAvailable.length,
      toolsCalled: report.toolsCalled.length,
      toolsMissingCoverage: (report.toolsMissingCoverage || []).length,
      failedSteps: (report.failedSteps || []).length,
    };

    console.log(JSON.stringify(output, null, 2));
    process.exit(report.ok ? 0 : 1);
  }
}

void run();
