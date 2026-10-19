import { Anchor, Paper, Stack, Table, Text } from "@mantine/core";
import { MAIN_INSTRUMENT_GROUPS } from "./mainInstruments";

function ChartLink({ symbol }) {
  const [exchange, ticker] = symbol.split(":");
  return (
    <div>
      <Anchor
        href={`https://www.tradingview.com/chart/?symbol=${encodeURIComponent(symbol)}`}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Открыть график ${symbol} в TradingView`}
        size="sm"
      >
        {ticker} ↗
      </Anchor>
      <Text size="xs" c="dimmed">
        {exchange}
      </Text>
    </div>
  );
}

export function MainInstrumentsTable() {
  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        Контракты и средние стопы из вашего списка. Ссылки открывают графики склеек и базовых
        активов в TradingView в новой вкладке.
      </Text>
      <Paper withBorder>
        <Table.ScrollContainer minWidth={800}>
          <Table
            verticalSpacing="sm"
            horizontalSpacing="md"
            highlightOnHover
            aria-label="Основные инструменты"
          >
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Инструмент</Table.Th>
                <Table.Th>Фьючерс</Table.Th>
                <Table.Th>Склейка</Table.Th>
                <Table.Th>Базовый актив</Table.Th>
                <Table.Th>Средний стоп</Table.Th>
              </Table.Tr>
            </Table.Thead>
            {MAIN_INSTRUMENT_GROUPS.map((group) => (
              <Table.Tbody key={group.name}>
                <Table.Tr bg="gray.0">
                  <Table.Th colSpan={5} scope="rowgroup">
                    {group.name}
                  </Table.Th>
                </Table.Tr>
                {group.instruments.map((instrument) => (
                  <Table.Tr key={instrument.contract}>
                    <Table.Th scope="row">{instrument.name}</Table.Th>
                    <Table.Td>
                      <Text size="sm" textWrap="nowrap">
                        {instrument.contract}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <ChartLink symbol={instrument.continuous} />
                    </Table.Td>
                    <Table.Td>
                      <Stack gap="xs">
                        {instrument.underlying.map((symbol) => (
                          <ChartLink key={symbol} symbol={symbol} />
                        ))}
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" textWrap="nowrap">
                        {instrument.averageStop}
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            ))}
          </Table>
        </Table.ScrollContainer>
      </Paper>
    </Stack>
  );
}
