import "./layout.css";
import { useState } from "react";

const LINKS = [["/", "▤", "Торговля"], ["/monthly", "▦", "По месяцам"], ["/journal", "✎", "Дневник трейдера"]];

export function Layout({ title, subtitle, action, children }) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("sidebar-collapsed") === "true"; } catch { return false; }
  });
  function toggleMenu() {
    setCollapsed(!collapsed);
    try { localStorage.setItem("sidebar-collapsed", String(!collapsed)); } catch { /* Storage is optional. */ }
  }
  return (
    <div className={`app-shell ${collapsed ? "menu-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-brand"><span aria-hidden="true">▥</span><strong className="menu-label">Trade Activity</strong></div>
        <button className="menu-toggle" onClick={toggleMenu} aria-expanded={!collapsed} aria-controls="main-navigation" aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"} title={collapsed ? "Развернуть меню" : "Свернуть меню"}>
          <span aria-hidden="true">{collapsed ? "→" : "←"}</span><span className="menu-label">Свернуть меню</span>
        </button>
        <nav id="main-navigation" aria-label="Главное меню">
          {LINKS.map(([href, icon, label]) => <a key={href} href={href} className={window.location.pathname === href ? "active" : ""} aria-current={window.location.pathname === href ? "page" : undefined} aria-label={label} title={label}><span aria-hidden="true">{icon}</span><span className="menu-label">{label}</span></a>)}
        </nav>
      </aside>
      <main>
        <header className="page-header"><div><h1>{title}</h1><span className="summary">{subtitle}</span></div>{action}</header>
        {children}
      </main>
    </div>
  );
}
