function readToken() {
  return localStorage.getItem('gita.token') || '';
}

function isJsonBody(body) {
  return body
    && !(body instanceof FormData)
    && !(body instanceof URLSearchParams)
    && !(body instanceof Blob)
    && typeof body !== 'string';
}

function detailToMessage(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .join('; ');
  }

  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object') return detail.msg || detail.message || JSON.stringify(detail);
  return null;
}

async function responseError(response) {
  let message = `Request failed (${response.status})`;

  try {
    const data = await response.json();
    message = detailToMessage(data.detail) || detailToMessage(data) || message;
  } catch {
    const text = await response.text().catch(() => '');
    if (text) message = text;
  }

  const error = new Error(message);
  error.status = response.status;
  throw error;
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = readToken();
  let body = options.body;

  if (token) headers.set('Authorization', `Bearer ${token}`);

  if (isJsonBody(body) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (isJsonBody(body)) {
    body = JSON.stringify(body);
  }

  const response = await fetch(path, {
    ...options,
    headers,
    body,
  });

  if (!response.ok) await responseError(response);
  if (response.status === 204) return null;

  const contentType = response.headers.get('content-type') || '';
  return contentType.includes('application/json') ? response.json() : response.blob();
}
