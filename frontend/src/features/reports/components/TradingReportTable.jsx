import { Table } from "@mantine/core";
import { Message } from "../../../shared/components/Message";
import { formatMoney, formatMonth, formatPercent, resultClass } from "../../../shared/format";

export function TradingReportTable({ rows, error, groupBy, loading }) {
  return (
    <div className="table-card">
      <Table striped highlightOnHover withTableBorder horizontalSpacing="md" verticalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{groupBy === "day" ? "День" : "Месяц"}</Table.Th>
            <Table.Th>Позиций</Table.Th>
            <Table.Th>Прибыльных</Table.Th>
            <Table.Th>Убыточных</Table.Th>
            <Table.Th>Итоговый винрейт</Table.Th>
            <Table.Th>Чистый винрейт</Table.Th>
            <Table.Th>Тейки</Table.Th>
            <Table.Th>Стопы</Table.Th>
            <Table.Th>Ручные</Table.Th>
            <Table.Th>Смешанные</Table.Th>
            <Table.Th>Не определено</Table.Th>
            <Table.Th>Результат</Table.Th>
            <Table.Th>Комиссия</Table.Th>
            <Table.Th>Чистыми</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((row) => (
            <Table.Tr key={`${row.period}-${row.currency}`}>
              <Table.Td>
                {row.period.length === 10
                  ? row.period.split("-").reverse().join(".")
                  : formatMonth(row.period)}
              </Table.Td>
              <Table.Td>{row.positions}</Table.Td>
              <Table.Td>{row.wins}</Table.Td>
              <Table.Td>{row.losses}</Table.Td>
              <Table.Td>{formatPercent(row.win_rate)}</Table.Td>
              <Table.Td>{formatPercent(row.clean_win_rate)}</Table.Td>
              <Table.Td>{row.takes}</Table.Td>
              <Table.Td>{row.stops}</Table.Td>
              <Table.Td>{row.manual}</Table.Td>
              <Table.Td>{row.mixed}</Table.Td>
              <Table.Td>{row.unknown}</Table.Td>
              <Table.Td className={resultClass(row.gross_result)}>
                {formatMoney(row.gross_result, row.currency)}
              </Table.Td>
              <Table.Td>{formatMoney(row.commission, row.currency)}</Table.Td>
              <Table.Td className={resultClass(row.net_result)}>
                {formatMoney(row.net_result, row.currency)}
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {loading && <Message>Загрузка отчёта…</Message>}
      {!loading && !error && rows.length === 0 && (
        <Message>Нет закрытых позиций для выбранных фильтров</Message>
      )}
    </div>
  );
}
