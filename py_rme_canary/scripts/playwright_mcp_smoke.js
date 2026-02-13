#!/usr/bin/env node
/*
 * Playwright MCP smoke checker.
 *
 * Usage:
 *   node py_rme_canary/scripts/playwright_mcp_smoke.js
 *
 * Optional env vars:
 *   PLAYWRIGHT_MCP_URL=http://localhost:8931/mcp
 *   PLAYWRIGHT_MCP_REPORT=.quality_reports/playwright_mcp_smoke_report.json
 *   PLAYWRIGHT_MCP_SCREENSHOT=.quality_reports/playwright_mcp_example_smoke.png
 */

const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

const localRequire = createRequire(__filename);
const mcpRequire = (() => {
  try {
    // Prefer local node_modules if available.
    localRequire.resolve("@modelcontextprotocol/sdk/client/index.js");
    return localRequire;
  } catch {
    // Fallback to dedicated MCP workspace installed under ~/.local.
    return createRequire("/home/marcelo/.local/playwright-mcp/package.json");
  }
})();

const { Client } = mcpRequire("@modelcontextprotocol/sdk/client/index.js");
const { StreamableHTTPClientTransport } = mcpRequire("@modelcontextprotocol/sdk/client/streamableHttp.js");

const mcpUrl = process.env.PLAYWRIGHT_MCP_URL || "http://localhost:8931/mcp";
const reportPath = process.env.PLAYWRIGHT_MCP_REPORT || ".quality_reports/playwright_mcp_smoke_report.json";
const screenshotPath = process.env.PLAYWRIGHT_MCP_SCREENSHOT || ".quality_reports/playwright_mcp_example_smoke.png";

function normalizeOutputPath(rawPath) {
  const resolved = path.resolve(rawPath);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  return resolved;
}

function summarizeToolResponse(response) {
  const content = response?.content || [];
  const textParts = content.filter(entry => entry?.type === "text").map(entry => entry?.text || "");
  return {
    isError: !!response?.isError,
    text: textParts.join("\n").slice(0, 5000),
  };
}

async function run() {
  const reportFile = normalizeOutputPath(reportPath);
  const screenshotFile = normalizeOutputPath(screenshotPath);

  const report = {
    ok: false,
    startedAt: new Date().toISOString(),
    mcpUrl,
    steps: [],
  };

  const client = new Client({ name: "playwright-mcp-smoke", version: "1.0.0" }, { capabilities: {} });
  const transport = new StreamableHTTPClientTransport(new URL(mcpUrl));

  try {
    await client.connect(transport);

    const toolsResp = await client.listTools();
    const tools = (toolsResp?.tools || []).map(tool => tool.name);
    report.toolsCount = tools.length;
    report.tools = tools;

    const navigateResp = await client.callTool({
      name: "browser_navigate",
      arguments: { url: "https://example.com" },
    });
    report.steps.push({ step: "browser_navigate", ...summarizeToolResponse(navigateResp) });

    const snapshotResp = await client.callTool({ name: "browser_snapshot", arguments: {} });
    report.steps.push({ step: "browser_snapshot", ...summarizeToolResponse(snapshotResp) });

    const screenshotResp = await client.callTool({
      name: "browser_take_screenshot",
      arguments: {
        type: "png",
        filename: path.basename(screenshotFile),
        fullPage: false,
      },
    });
    report.steps.push({ step: "browser_take_screenshot", ...summarizeToolResponse(screenshotResp) });

    const closeResp = await client.callTool({ name: "browser_close", arguments: {} });
    report.steps.push({ step: "browser_close", ...summarizeToolResponse(closeResp) });

    report.ok = report.steps.every(step => !step.isError);
  } catch (error) {
    report.error = String(error?.stack || error);
  } finally {
    try {
      await client.close();
    } catch {
      // ignore close errors
    }
    report.finishedAt = new Date().toISOString();
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2), "utf-8");
    console.log(
      JSON.stringify(
        {
          ok: report.ok,
          mcpUrl,
          reportPath: reportFile,
          screenshotPath: screenshotFile,
          toolsCount: report.toolsCount || 0,
        },
        null,
        2,
      ),
    );
    process.exit(report.ok ? 0 : 1);
  }
}

void run();
