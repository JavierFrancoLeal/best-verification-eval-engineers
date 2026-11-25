// Layer 1 CPU True Negative: Node.js integration harness with real process spawn,
// bounded readiness polling, real behavioral assertions, and best-effort teardown.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForHealth(url, timeoutMs = 5000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url);
      if (res.ok) return await res.json();
    } catch {}
    await sleep(50);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

export async function runIntegrationSmoke(serverEntry) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "svc-int-"));
  const child = spawn(process.execPath, [serverEntry], { stdio: "ignore" });
  try {
    const health = await waitForHealth("http://127.0.0.1:4199/health");
    assert.strictEqual(health.status, "ok");
  } finally {
    try {
      child.kill("SIGKILL");
    } catch {}
    try {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch {}
  }
}
