import { useCallback, useState } from "react";
import { notifications } from "@mantine/notifications";

export function notifySuccess(message, title = "Готово") {
  notifications.show({ title, message, color: "green", autoClose: 8000, withCloseButton: true });
}

export function useNotificationError() {
  const [error, setError] = useState("");
  const reportError = useCallback((message) => {
    setError(message);
    if (message) notifications.show({ id: `error-${message}`, title: "Не удалось выполнить действие", message, color: "red", autoClose: false, withCloseButton: true });
  }, []);
  return [error, reportError];
}
