export function createRequestQueue() {
  let pending = Promise.resolve();
  return (operation) => {
    const result = pending.then(operation);
    pending = result.catch(() => {});
    return result;
  };
}
