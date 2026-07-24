import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${path}`, {
      headers: { accept: "text/html", host: "localhost" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the RoomPulse dashboard shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>RoomPulse — Ask Your Room<\/title>/i);
  assert.match(html, /Your room,/);
  assert.match(html, /now/);
  assert.match(html, /queryable\./);
  assert.match(html, /PHYSICAL DATA · GROUNDED AI/);
  assert.match(html, /The room has a rhythm\./);
  assert.match(html, /ASK WITH CODEX OR CHATGPT/);
  assert.match(
    html,
    /<meta property="og:image" content="http:\/\/localhost\/og\.png"/i,
  );
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/i);
});

test("removes all starter-only assets and dependencies", async () => {
  const packageJson = await readFile(
    new URL("../package.json", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.doesNotReject(access(new URL("../public/og.png", import.meta.url)));
});

