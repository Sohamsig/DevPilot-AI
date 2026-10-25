import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { once } from "node:events";
import { fileURLToPath } from "node:url";

const cli = fileURLToPath(new URL("../src/index.js", import.meta.url));

function runCli(args, env = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cli, ...args], {
      encoding: "utf8",
      env: { ...process.env, ...env },
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });

    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("CLI process timed out"));
    }, 10000);

    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.on("close", (status) => {
      clearTimeout(timer);
      resolve({ status, stdout, stderr });
    });
  });
}

async function withMockServer(handler, callback) {
  const server = createServer(handler);
  server.listen(0, "127.0.0.1");
  await once(server, "listening");

  try {
    const address = server.address();
    await callback(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise((resolve, reject) =>
      server.close((error) => error ? reject(error) : resolve())
    );
  }
}

test("help displays available commands", async () => {
  const result = await runCli(["--help"]);
  assert.equal(result.status, 0);
  assert.match(result.stdout, /devpilot doctor/);
  assert.match(result.stdout, /devpilot run/);
});

test("version displays the current version", async () => {
  const result = await runCli(["--version"]);
  assert.equal(result.status, 0);
  assert.match(result.stdout, /0\.1\.0/);
});

test("unknown commands fail clearly", async () => {
  const result = await runCli(["not-a-command"]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Unknown command/);
});

test("doctor reports a healthy API", async () => {
  await withMockServer((req, res) => {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({
      status: "ok",
      service: "devpilot-ai",
      version: "0.7.0",
    }));
  }, async (url) => {
    const result = await runCli(["doctor"], { DEVPILOT_URL: url });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /DevPilot AI: ok/);
    assert.match(result.stdout, /Version: 0\.7\.0/);
  });
});

test("doctor reports API errors", async () => {
  await withMockServer((req, res) => {
    res.writeHead(503, { "content-type": "application/json" });
    res.end(JSON.stringify({ detail: "Service unavailable" }));
  }, async (url) => {
    const result = await runCli(["doctor"], { DEVPILOT_URL: url });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Service unavailable/);
  });
});

test("doctor reports an unreachable service", async () => {
  const result = await runCli(["doctor"], {
    DEVPILOT_URL: "http://127.0.0.1:1",
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Cannot reach DevPilot AI/);
});
