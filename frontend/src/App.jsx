import { MonthlyPage } from "./pages/MonthlyPage";
import { PositionsPage } from "./pages/PositionsPage";


export default function App() {
  return window.location.pathname === "/monthly" ? <MonthlyPage /> : <PositionsPage />;
}

