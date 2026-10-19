import assert from "node:assert/strict";
import test from "node:test";
import { exitReasonLabel } from "../src/features/trading/model.js";

test("exit labels distinguish assessed exits from the legacy manual fallback", () => {
  for (const [reason, label] of [
    ["stop", "Стоп-лосс"],
    ["take", "Тейк-профит"],
    ["manual", "Вышел руками"],
    ["mixed", "Смешанный выход"],
    ["unknown", "Не определено"],
  ]) {
    assert.equal(
      exitReasonLabel({ status: "closed", exit_assessment: { reason, source: "plan_prices" } }),
      label,
    );
  }
  assert.equal(
    exitReasonLabel({
      status: "closed",
      exit_assessment: { reason: "manual", source: "default_rule" },
    }),
    "Не определено",
  );
  assert.equal(exitReasonLabel({ status: "closed" }), "Не определено");
  assert.equal(exitReasonLabel({ status: "open" }), "Позиция открыта");
});
