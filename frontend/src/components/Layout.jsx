export function Layout({ title, subtitle, action, children }) {
  const path = window.location.pathname;

  return (
    <main>
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          <span className="summary">{subtitle}</span>
        </div>

        <nav>
          <a className={path === "/" ? "active" : ""} href="/">Позиции</a>
          <a className={path === "/monthly" ? "active" : ""} href="/monthly">По месяцам</a>
        </nav>

        {action}
      </header>
      {children}
    </main>
  );
}

