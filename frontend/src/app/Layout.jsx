import { useState } from "react";
import { AppShell, Button, Group, NavLink, Stack, Text, Title, Tooltip } from "@mantine/core";

const LINKS = [["/", "▤", "Торговля"], ["/monthly", "▦", "По месяцам"], ["/journal", "✎", "Дневник трейдера"]];

export function Layout({ title, subtitle, action, children }) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("sidebar-collapsed") === "true"; } catch { return false; }
  });
  function toggleMenu() {
    setCollapsed(!collapsed);
    try { localStorage.setItem("sidebar-collapsed", String(!collapsed)); } catch { /* Storage is optional. */ }
  }
  return <AppShell navbar={{ width: collapsed ? 76 : 230, breakpoint: 0 }} padding="lg">
    <AppShell.Navbar p="sm">
      <Stack gap="lg">
        <Text fw={700} size="lg" ta="center">{collapsed ? "▥" : "Trade Activity"}</Text>
        <Button variant="subtle" onClick={toggleMenu} aria-expanded={!collapsed} aria-controls="main-navigation" aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"}>{collapsed ? "→" : "← Свернуть меню"}</Button>
        <nav id="main-navigation" aria-label="Главное меню">
          {LINKS.map(([href, icon, label]) => <Tooltip key={href} label={label} disabled={!collapsed} position="right">
            <NavLink href={href} label={collapsed ? icon : label} leftSection={collapsed ? null : icon} active={window.location.pathname === href} aria-label={label} aria-current={window.location.pathname === href ? "page" : undefined} />
          </Tooltip>)}
        </nav>
      </Stack>
    </AppShell.Navbar>
    <AppShell.Main>
      <Group justify="space-between" mb="lg"><div><Title order={1} size="h2">{title}</Title>{subtitle && <Text c="dimmed" size="sm">{subtitle}</Text>}</div>{action}</Group>
      {children}
    </AppShell.Main>
  </AppShell>;
}
