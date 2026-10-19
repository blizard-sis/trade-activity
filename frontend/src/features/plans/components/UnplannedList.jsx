import { Badge, Button, Text } from "@mantine/core";
import { formatDate, formatMoney, resultClass } from "../../../shared/format";
import { directionLabel } from "../model";

export function UnplannedList({ positions, loading, onCreate }) {
  return (
    <div className="plan-list">
      {positions.map((position) => (
        <div key={position.id} className="plan-list-item unplanned">
          <span className="plan-list-top">
            <strong>{position.ticker || position.instrument_name}</strong>
            <Badge
              size="xs"
              color={position.status === "closed" ? "dark" : "green"}
              variant="light"
            >
              {position.status === "closed" ? "Закрыта" : "Открыта"}
            </Badge>
          </span>
          <span className="plan-list-meta">
            {position.account_name} · {directionLabel(position.direction)} ·{" "}
            {formatDate(position.entry_at)}
          </span>
          <span className={resultClass(position.net_result)}>
            {formatMoney(position.net_result, position.result_currency)}
          </span>
          <Button size="xs" variant="light" type="button" onClick={() => onCreate(position)}>
            Создать план
          </Button>
        </div>
      ))}
      {loading && (
        <Text c="dimmed" size="sm" p="md">
          Загрузка позиций…
        </Text>
      )}
      {!loading && !positions.length && (
        <Text c="dimmed" size="sm" p="md">
          Все позиции уже привязаны к планам.
        </Text>
      )}
    </div>
  );
}
