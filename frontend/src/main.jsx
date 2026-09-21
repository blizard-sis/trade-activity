import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import { Notifications } from "@mantine/notifications";
import "./shared/styles.css";
import { MantineProvider } from "@mantine/core";
import { theme } from "./app/theme";
import App from "./app/App";


createRoot(document.getElementById("root")).render(
  <StrictMode>
    <MantineProvider theme={theme} forceColorScheme="light"><Notifications position="top-right" zIndex={2000} limit={3} /><App /></MantineProvider>
  </StrictMode>,
);

