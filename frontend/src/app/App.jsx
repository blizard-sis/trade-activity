import { lazy, Suspense } from "react";
import routes from "./routes.json";
import { Message } from "../shared/components/Message";
import { Layout } from "./Layout";

const pages = {
  trading: lazy(() =>
    import("../features/trading/PositionsPage").then((module) => ({
      default: module.PositionsPage,
    })),
  ),
  reports: lazy(() =>
    import("../features/reports/TradingReportPage").then((module) => ({
      default: module.TradingReportPage,
    })),
  ),
  journal: lazy(() =>
    import("../features/plans/PlansPage").then((module) => ({ default: module.PlansPage })),
  ),
  "data-transfer": lazy(() =>
    import("../features/data-transfer/DataTransferPage").then((module) => ({
      default: module.DataTransferPage,
    })),
  ),
  settings: lazy(() =>
    import("../features/settings/SettingsPage").then((module) => ({
      default: module.SettingsPage,
    })),
  ),
};

export default function App() {
  const route = routes.find(({ path, aliases = [] }) =>
    [path, ...aliases].includes(window.location.pathname),
  );
  if (!route) {
    return (
      <Layout title="Страница не найдена">
        <Message>
          <a href="/">Перейти в торговлю</a>
        </Message>
      </Layout>
    );
  }
  const Page = pages[route.id];
  return (
    <Suspense
      fallback={
        <Layout title={route.label}>
          <Message>Загрузка раздела…</Message>
        </Layout>
      }
    >
      <Page />
    </Suspense>
  );
}
