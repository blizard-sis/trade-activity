export async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Ошибка запроса: ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}


export async function download(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Ошибка запроса: ${response.status}`);
  }
  return response.blob();
}


export function queryString(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) value.forEach((item) => params.append(key, item));
    else if (value !== "" && value !== null && value !== undefined) params.set(key, value);
  });
  return params.toString();
}
