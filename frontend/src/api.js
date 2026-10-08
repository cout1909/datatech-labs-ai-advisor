const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
let historyToken;
function sessionToken() {
  if (historyToken) return historyToken;
  try { historyToken = localStorage.getItem('datatech-advisor-session'); } catch { /* In-memory session when storage is unavailable. */ }
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(historyToken || '')) {
    historyToken = crypto.randomUUID();
    try { localStorage.setItem('datatech-advisor-session', historyToken); } catch { /* History remains available until this tab closes. */ }
  }
  return historyToken;
}
export async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), path === '/api/analyze' ? 70000 : 15000);
  try {
    const response = await fetch(`${base}${path}`, { ...options, headers: { ...options.headers, 'X-Session-ID': sessionToken() }, signal: controller.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check your input and try again.');
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The server took too long to respond. It may be waking up; please try again.');
    if (error instanceof TypeError) throw new Error('Cannot reach the advisor backend. Check your connection and try again.');
    throw error;
  } finally { clearTimeout(timer); }
}
