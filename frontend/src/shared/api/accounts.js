import { request } from "./client";

export const loadAccounts = (options) => request("/api/accounts", options);
