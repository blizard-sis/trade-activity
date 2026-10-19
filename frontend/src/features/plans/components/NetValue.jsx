import { Fragment } from "react";
import { formatMoney, resultClass } from "../../../shared/format";
import { netParts } from "../model";

export function NetValue({ summary }) {
  const parts = netParts(summary);
  if (!parts.length) return "—";
  return parts.map(([currency, value], index) => (
    <Fragment key={currency}>
      {index > 0 ? " · " : null}
      <span className={resultClass(value)}>{formatMoney(value, currency)}</span>
    </Fragment>
  ));
}
