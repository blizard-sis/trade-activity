export function Message({ children, type = "empty" }) {
  return <div className={`message ${type}`}>{children}</div>;
}

