import { Alert, Button, Paper, SimpleGrid, Stack, Text, Title } from "@mantine/core";
import { Layout } from "../../app/Layout";
import { PositionFilters } from "../../shared/positions/PositionFilters";
import { TradingViewImport } from "./TradingViewImport";
import { useDataTransfer } from "./useDataTransfer";
import "./data-transfer.css";

export function DataTransferPage() {
  const {
    accounts,
    filters,
    error,
    importing,
    exporting,
    importTradingView,
    exportPositions,
    updateFilter,
  } = useDataTransfer();
  return (
    <Layout
      title="Импорт и экспорт"
      subtitle="Загрузка сделок из TradingView и выгрузка позиций в JSON"
    >
      <Stack gap="lg">
        {error && <Alert color="red">{error}</Alert>}
        <TradingViewImport importing={importing} onImport={importTradingView} />
        <Paper withBorder p="lg" component="section" aria-label="Экспорт позиций">
          <Stack>
            <Title order={2} size="h3">
              Экспорт JSON
            </Title>
            <Text size="sm" c="dimmed">
              Без фильтров выгружаются все позиции. Чтобы ограничить выгрузку, выберите счета,
              период или инструмент.
            </Text>
            <SimpleGrid className="position-filter-grid" cols={{ base: 1, sm: 2, lg: 3 }}>
              <PositionFilters
                accounts={accounts}
                filters={filters}
                onChange={updateFilter}
                withLabels
              />
            </SimpleGrid>
            <Button
              loading={exporting}
              onClick={exportPositions}
              style={{ alignSelf: "flex-start" }}
            >
              Выгрузить JSON
            </Button>
          </Stack>
        </Paper>
      </Stack>
    </Layout>
  );
}
