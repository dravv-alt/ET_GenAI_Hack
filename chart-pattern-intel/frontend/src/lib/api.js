// Backend API wrapper (switch between mock and live)
export const USE_MOCK = false;

const BASE_URL = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8002';

async function request(path) {
  const resp = await fetch(`${BASE_URL}${path}`);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed: ${resp.status}`);
  }
  return resp.json();
}

export function fetchChart(ticker, period = '6mo', market = 'NSE') {
  return request(`/chart/${ticker}?period=${period}&market=${market}`);
}

export function fetchPatterns(ticker, period = '1y', market = 'NSE', mtf = false) {
  return request(`/patterns/${ticker}?period=${period}&market=${market}&mtf=${mtf}`);
}

export function fetchBacktest(ticker, patternType, market = 'NSE') {
  return request(`/backtest/${ticker}/${patternType}?market=${market}`);
}

export async function fetchScan(tickers, period = '6mo', limit = 20, market = 'NSE', mtf = false) {
  const resp = await fetch(`${BASE_URL}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tickers, period, limit, market, mtf })
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed: ${resp.status}`);
  }
  return resp.json();
}

export async function fetchExplain(pattern, backtest) {
  const resp = await fetch(`${BASE_URL}/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pattern, backtest })
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed: ${resp.status}`);
  }
  return resp.json();
}
