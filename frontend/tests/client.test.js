import assert from "node:assert/strict";
import test from "node:test";
import { download, queryString, request, writeJson } from "../src/shared/api/client.js";

test("filters preserve multiple accounts and omit empty values", () => {
  const query = new URLSearchParams(
    queryString({ account: ["a", "b"], search: "S&P", from: "", to: null, status: undefined }),
  );
  assert.deepEqual(query.getAll("account"), ["a", "b"]);
  assert.equal(query.get("search"), "S&P");
  assert.equal(query.size, 3);
});

test("JSON writes pass data and the abort signal, and accept an empty response", async (context) => {
  const controller = new AbortController();
  const fetch = context.mock.method(
    globalThis,
    "fetch",
    async () => new Response(null, { status: 204 }),
  );
  const body = { note: "Разбор сделки" };
  assert.equal(await writeJson("/api/example", "PUT", body, { signal: controller.signal }), null);
  const [path, options] = fetch.mock.calls[0].arguments;
  assert.equal(path, "/api/example");
  assert.equal(options.method, "PUT");
  assert.equal(options.headers["Content-Type"], "application/json");
  assert.deepEqual(JSON.parse(options.body), body);
  assert.equal(options.signal, controller.signal);
});

test("JSON and file requests report API errors and tolerate non-JSON error pages", async (context) => {
  for (const read of [request, download]) {
    for (const [body, message] of [
      [JSON.stringify({ error: "Не удалось выполнить запрос" }), /Не удалось выполнить запрос/],
      ["<html>Bad gateway</html>", /Ошибка запроса: 502/],
      ["null", /Ошибка запроса: 502/],
    ]) {
      const fetch = context.mock.method(
        globalThis,
        "fetch",
        async () => new Response(body, { status: 502 }),
      );
      await assert.rejects(read("/api/example"), message);
      fetch.mock.restore();
    }
  }
});

test("JSON and file requests retain their response formats", async (context) => {
  context.mock.method(globalThis, "fetch", async () => new Response('{"positions":[]}'));
  assert.deepEqual(await request("/api/example"), { positions: [] });
  assert.equal(await (await download("/api/example")).text(), '{"positions":[]}');
});
