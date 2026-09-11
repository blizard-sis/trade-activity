import { MonthlyPage } from "../features/reports/MonthlyPage";
import { PositionsPage } from "../features/trading/PositionsPage";
import { JournalPage } from "../features/journal/JournalPage";


export default function App() {
  if (window.location.pathname === "/journal") return <JournalPage />;
  return window.location.pathname === "/monthly" ? <MonthlyPage /> : <PositionsPage />;
}
