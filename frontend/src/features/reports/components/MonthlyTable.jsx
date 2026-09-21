import { Table } from "@mantine/core";
import { Message } from "../../../shared/components/Message";
import { formatMoney, formatMonth, resultClass } from "../../../shared/format";
import { formatPercent as percent } from "../../../shared/format";

export function MonthlyTable({ months, error }) {
  return (
      <div className="table-card">
        <Table striped highlightOnHover withTableBorder horizontalSpacing="md" verticalSpacing="sm">
          <Table.Thead><Table.Tr>
            <Table.Th>Месяц</Table.Th><Table.Th>Позиций</Table.Th><Table.Th>Прибыльных</Table.Th><Table.Th>Убыточных</Table.Th>
            <Table.Th>Итоговый винрейт</Table.Th><Table.Th>Чистый винрейт</Table.Th><Table.Th>Тейки</Table.Th><Table.Th>Стопы</Table.Th><Table.Th>Ручные</Table.Th><Table.Th>Смешанные</Table.Th><Table.Th>Не определено</Table.Th><Table.Th>Результат</Table.Th><Table.Th>Комиссия</Table.Th><Table.Th>Чистыми</Table.Th>
          </Table.Tr></Table.Thead>
          <Table.Tbody>
            {months.map((row) => (
              <Table.Tr key={`${row.month}-${row.currency}`}>
                <Table.Td>{formatMonth(row.month)}</Table.Td><Table.Td>{row.positions}</Table.Td><Table.Td>{row.wins}</Table.Td><Table.Td>{row.losses}</Table.Td>
                <Table.Td>{percent(row.win_rate)}</Table.Td><Table.Td>{percent(row.clean_win_rate)}</Table.Td>
                <Table.Td>{row.takes}</Table.Td><Table.Td>{row.stops}</Table.Td><Table.Td>{row.manual}</Table.Td><Table.Td>{row.mixed}</Table.Td><Table.Td>{row.unknown}</Table.Td>
                <Table.Td className={resultClass(row.gross_result)}>{formatMoney(row.gross_result, row.currency)}</Table.Td>
                <Table.Td>{formatMoney(row.commission, row.currency)}</Table.Td>
                <Table.Td className={resultClass(row.net_result)}>{formatMoney(row.net_result, row.currency)}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {!error && months.length === 0 && <Message>Нет закрытых позиций для выбранных фильтров</Message>}
      </div>
  );
}
