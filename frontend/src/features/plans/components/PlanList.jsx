import { Text, UnstyledButton } from "@mantine/core";
import { formatDate } from "../../../shared/format";
import { planMeta } from "../model";
import { NetValue } from "./NetValue";

export function PlanList({ plans, selectedId, onSelect }) {
  return (
    <div className="plan-list">
      {plans.map((plan) => {
        const selected = plan.id === selectedId;
        return (
          <UnstyledButton
            type="button"
            key={plan.id}
            className={`plan-list-item ${selected ? "active" : ""}`}
            onClick={() => onSelect(plan.id)}
            aria-current={selected ? "true" : undefined}
          >
            <span className="plan-list-copy">
              <span className="plan-list-row">
                <span className="plan-list-title">{plan.title}</span>
                <span className="plan-list-result">
                  <NetValue summary={plan.summary} />
                </span>
              </span>
              <span className="plan-list-meta">{planMeta(plan)}</span>
              <span className="plan-list-meta">
                {formatDate(plan.summary?.last_exit_at || plan.created_at)}
              </span>
            </span>
          </UnstyledButton>
        );
      })}
      {!plans.length && (
        <Text c="dimmed" size="sm" p="md">
          Планов пока нет. Создайте первый план.
        </Text>
      )}
    </div>
  );
}
