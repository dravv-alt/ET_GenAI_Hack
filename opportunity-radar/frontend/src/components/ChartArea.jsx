import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

// Generate realistic looking mock OHLC data
const generateMockData = (basePrice, numDays) => {
  let data = [];
  let time = new Date('2025-01-01').getTime();
  let currentPrice = basePrice;
  
  for (let i = 0; i < numDays; i++) {
    // Generate daily volatility
    const volatility = currentPrice * 0.02; // max 2% swing
    const open = currentPrice + (Math.random() - 0.5) * volatility;
    const high = open + Math.random() * volatility;
    const low = open - Math.random() * volatility;
    const close = open + (Math.random() - 0.5) * volatility * 1.5;
    
    // Make sure high and low are actually the max and min
    const finalHigh = Math.max(open, close, high);
    const finalLow = Math.min(open, close, low);
    
    // Format required by lightweight-charts (string format 'yyyy-mm-dd' or timestamp in sec)
    const timestampObj = new Date(time);
    const timeStr = timestampObj.toISOString().split('T')[0];
    
    data.push({
      time: timeStr,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(finalHigh.toFixed(2)),
      low: parseFloat(finalLow.toFixed(2)),
      close: parseFloat(close.toFixed(2))
    });
    
    currentPrice = close;
    time += 24 * 60 * 60 * 1000;
    
    // Skip weekends roughly by adding 2 days if it's Friday (approximating day of week with simple modulo is tricky, we just use valid dates for lightweight charts, it handles gaps automatically in date string mode)
    if (timestampObj.getDay() === 5) {
      time += 2 * 24 * 60 * 60 * 1000;
    }
  }
  return data;
};

const markerFromAlert = (alert) => {
  const typeStr = alert?.alert_type || alert?.type || '';
  const isBearish = typeStr.includes('sell') || typeStr.includes('miss');
  const isBullish = typeStr.includes('buy') || typeStr.includes('beat');
  
  return {
    time: new Date().toISOString().split('T')[0], 
    position: isBearish ? 'aboveBar' : 'belowBar',
    color: isBearish ? '#dc2626' : isBullish ? '#16a34a' : '#d97706',
    shape: isBearish ? 'arrowDown' : 'arrowUp',
    text: (typeStr || 'SIGNAL').toUpperCase().replace('_', ' '),
    size: 1,
  };
};

const ChartArea = ({ ticker, alerts }) => {
  const chartContainerRef = useRef();
  const [lastPrice, setLastPrice] = useState(0);
  const [pctChange, setPctChange] = useState(0);
  
  useEffect(() => {
    if (!chartContainerRef.current) return;
    
    chartContainerRef.current.innerHTML = '';
    
    let containerWidth = chartContainerRef.current.clientWidth;
    if (containerWidth === 0) containerWidth = 600; // fallback if not painted yet
    
    const chartOptions = {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#555555',
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        vertLine: { color: '#1a1a1a', width: 1, style: 3 },
        horzLine: { color: '#1a1a1a', width: 1, style: 3 },
      },
      rightPriceScale: { borderColor: '#d8d8d8' },
      timeScale: { borderColor: '#d8d8d8' },
      width: containerWidth,
      height: 380,
    };

    const chart = createChart(chartContainerRef.current, chartOptions);
    
    const candlestickOptions = {
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
    };
    
    const candlestickSeries = chart.addCandlestickSeries(candlestickOptions);
    
    const hashTicker = ticker ? ticker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) : 100;
    const basePrice = 100 + (hashTicker % 2000); 
    const ohlcData = generateMockData(basePrice, 120);
    
    const currentDay = ohlcData[ohlcData.length - 1];
    const prevDay = ohlcData[ohlcData.length - 2] || currentDay;
    const change = ((currentDay.close - prevDay.close) / prevDay.close) * 100;
    
    setLastPrice(currentDay.close);
    setPctChange(change);
    
    candlestickSeries.setData(ohlcData);
    
    if (alerts && alerts.length > 0) {
      try {
        const latestAlert = alerts[0];
        if (latestAlert) {
          const marker = {
            ...markerFromAlert(latestAlert),
            time: ohlcData[ohlcData.length - 1].time
          };
          candlestickSeries.setMarkers([marker]);
        }
      } catch (err) {
        console.error("Marker error:", err);
      }
    }
    
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current) {
         chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ticker, alerts]);

  const chgColor = pctChange >= 0 ? 'var(--green)' : 'var(--red)';
  const chgPrefix = pctChange >= 0 ? '+' : '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '12px 16px', background: '#fff', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.04em' }}>
            {ticker || 'UNKNOWN'}
          </span>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 18, fontWeight: 500, color: 'var(--text-primary)' }}>
            ₹{lastPrice.toFixed(2)}
          </span>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 14, fontWeight: 500, color: chgColor }}>
            {chgPrefix}{pctChange.toFixed(2)}%
          </span>
        </div>
      </div>
      
      <div style={{ background: '#fff', minHeight: 380 }} ref={chartContainerRef} />
    </div>
  );
};

export default ChartArea;
