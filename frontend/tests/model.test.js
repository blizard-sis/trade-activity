import test from "node:test";
import assert from "node:assert/strict";
import { summarizeMonths } from "../src/features/reports/model.js";
import { createRequestQueue } from "../src/shared/api/queue.js";

test("report totals weight positions and keep currencies separate", () => {
  const result = summarizeMonths([
    { positions: 2, wins: 2, takes: 1, stops: 0, currency: "USD", net_result: 10 },
    { positions: 8, wins: 0, takes: 1, stops: 2, currency: "RUB", net_result: -20 },
    { positions: 0, wins: 0, takes: 0, stops: 0, currency: "USD", net_result: 5 },
  ]);
  assert.deepEqual(result, { takes: 2, stops: 2, net: { USD: 15, RUB: -20 }, winRate: 20, cleanWinRate: 50 });
  assert.deepEqual(summarizeMonths([]), { takes: 0, stops: 0, net: {}, winRate: null, cleanWinRate: null });
});

test("settings writes wait for preceding operations and recover after failure", async () => {
  const enqueue = createRequestQueue();
  const events = [];
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  const first = enqueue(async () => { events.push("save"); await gate; throw new Error("offline"); });
  const rejected = assert.rejects(first, /offline/);
  const second = enqueue(() => { events.push("reset"); return "done"; });
  await Promise.resolve();
  assert.deepEqual(events, ["save"]);
  release();
  await rejected;
  assert.equal(await second, "done");
  assert.deepEqual(events, ["save", "reset"]);
});
