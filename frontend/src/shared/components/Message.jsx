import { Alert } from "@mantine/core";

export function Message({ type, children }) {
  return <Alert color={type === "error" ? "red" : "blue"} my="sm" role={type === "error" ? "alert" : "status"}>{children}</Alert>;
}
