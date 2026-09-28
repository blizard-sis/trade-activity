import { Table, UnstyledButton } from "@mantine/core";
import { Message } from "../../../shared/components/Message";
import { POSITION_COLUMNS } from "../columns";

export function PositionsTable({ positions, visibleColumns, onSort, error, loading }) {
  const selectedPosition = new URLSearchParams(window.location.search).get("position");
  const displayedColumns = POSITION_COLUMNS.filter((column) => visibleColumns.includes(column.key));
  return (
    <div className="table-card" aria-busy={loading}>
      <Table
        className="positions-table"
        striped
        highlightOnHover
        withTableBorder
        horizontalSpacing="md"
        verticalSpacing="sm"
      >
        <Table.Thead>
          <Table.Tr>
            {displayedColumns.map((column) => (
              <Table.Th
                key={column.key}
                className={`${column.sort ? "sortable" : ""} ${column.align || ""}`}
              >
                {column.sort ? (
                  <UnstyledButton fw={600} fz="xs" onClick={() => onSort(column.sort)}>
                    {column.label}
                  </UnstyledButton>
                ) : (
                  column.label
                )}
              </Table.Th>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {positions.map((position) => (
            <Table.Tr
              key={position.id}
              id={`position-${position.id}`}
              className={selectedPosition === position.id ? "selected-position" : ""}
            >
              {displayedColumns.map((column) => (
                <Table.Td key={column.key} className={column.align || ""}>
                  {column.render(position)}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {loading && <Message>Загрузка позиций…</Message>}
      {error && (
        <Message>
          Не удалось загрузить позиции. Попробуйте изменить фильтры или обновить страницу.
        </Message>
      )}
      {!loading && !error && positions.length === 0 && (
        <Message>Нет позиций для выбранных фильтров</Message>
      )}
    </div>
  );
}
