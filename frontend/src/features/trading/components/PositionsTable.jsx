import { Message } from "../../../shared/components/Message";
import { createColumns } from "../columns";

export function PositionsTable({ positions, visibleColumns, onSort, error }) {
  const displayedColumns = createColumns().filter((column) => visibleColumns.includes(column.key));
  return (
    <div className="table-card">
      <table className="positions-table">
        <thead><tr>
          {displayedColumns.map((column) => (
            <th
              key={column.key}
              className={`${column.sort ? "sortable" : ""} ${column.align || ""}`}
              onClick={column.sort ? () => onSort(column.sort) : undefined}
            >
              {column.label}
            </th>
          ))}
        </tr></thead>
        <tbody>
          {positions.map((position) => (
            <tr key={position.id} id={`position-${position.id}`} className={new URLSearchParams(window.location.search).get("position") === position.id ? "selected-position" : ""}>
              {displayedColumns.map((column) => (
                <td key={column.key} className={column.align || ""}>{column.render(position)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!error && positions.length === 0 && <Message>Нет позиций для выбранных фильтров</Message>}
    </div>
  );
}
