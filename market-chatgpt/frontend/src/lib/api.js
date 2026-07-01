const API_BASE = 'http://localhost:8003';

export const parsePortfolio = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}/portfolio/parse`, {
    method: 'POST',
    body: formData,
  });
  
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || 'Failed to parse portfolio');
  }
  
  return await res.json();
};

export const fetchMarketData = async (exchange = 'NIFTY') => {
  const res = await fetch(`${API_BASE}/market/live?exchange=${exchange}`);
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || 'Failed to fetch live market data');
  }
  return await res.json();
};
