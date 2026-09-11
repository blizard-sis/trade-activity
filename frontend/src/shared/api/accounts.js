import { request } from "./client";

export const loadAccounts = () => request("/api/accounts");
