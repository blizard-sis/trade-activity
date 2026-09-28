import { StrictMode } from "react";
import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { createRoot } from "react-dom/client";
import App from "./app/App";
import { theme } from "./app/theme";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "./shared/styles.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <MantineProvider theme={theme} forceColorScheme="light">
      <Notifications position="top-right" zIndex={2000} limit={3} />
      <App />
    </MantineProvider>
  </StrictMode>,
);
