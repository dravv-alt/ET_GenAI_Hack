import { useEffect, useRef } from 'react';
import { createChart, CrosshairMode } from 'lightweight-charts';

const BEARISH_TYPES = ['double_top', 'head_shoulders'];

export default function CandlestickChart({ ohlcv = [], levels = [], patterns = [], height = 240, formatPrice }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const priceLinesRef = useRef([]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#888888',
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#1a1a1a', width: 1, style: 3 },
        horzLine: { color: '#1a1a1a', width: 1, style: 3 },
      },
      rightPriceScale: { borderColor: '#d8d8d8', scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: '#d8d8d8', timeVisible: true, secondsVisible: false },
    });
    const series = chart.addCandlestickSeries({
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth || 600 });
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = ohlcv.map((row) => ({
      time: row.date,
      open: row.open,
      high: row.high,
      low: row.low,
      close: row.close,
    }));
    seriesRef.current.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [ohlcv]);

  useEffect(() => {
    if (!seriesRef.current) return;
    priceLinesRef.current.forEach((line) => {
      try {
        seriesRef.current.removePriceLine(line);
      } catch {
        // ignore if line is already removed
      }
    });
    priceLinesRef.current = [];
    levels.forEach((level) => {
      const line = seriesRef.current.createPriceLine({
        price: level.price,
        color: level.level_type === 'support' ? '#16a34a' : '#dc2626',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
      });
      priceLinesRef.current.push(line);
    });
  }, [levels]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const markers = patterns
      .filter((pattern) => pattern.detected_on)
      .map((pattern) => {
        const bearish = BEARISH_TYPES.includes(pattern.pattern_type);
        return {
          time: pattern.detected_on,
          position: bearish ? 'aboveBar' : 'belowBar',
          color: bearish ? '#dc2626' : '#16a34a',
          shape: bearish ? 'arrowDown' : 'arrowUp',
          text: pattern.pattern_type.replace('_', ' '),
        };
      });
    seriesRef.current.setMarkers(markers);
  }, [patterns]);

  return (
    <div className="chart-wrap" style={{ display: 'grid', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.10em', color: 'var(--text-muted)' }}>
          CANDLESTICK CHART
        </div>
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          {ohlcv.length ? `${ohlcv.length} BARS` : 'NO DATA'}
        </div>
      </div>
      <div ref={containerRef} style={{ width: '100%', height }} />
      {!ohlcv.length && (
        <div className="chart-empty">AWAITING DATA</div>
      )}
      {ohlcv.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>DATE</th>
              <th>OPEN</th>
              <th>HIGH</th>
              <th>LOW</th>
              <th>CLOSE</th>
              <th>VOL</th>
            </tr>
          </thead>
          <tbody>
            {ohlcv.slice(-6).map((row) => (
              <tr key={row.date}>
                <td>{row.date}</td>
                <td>{formatPrice ? formatPrice(row.open) : row.open.toFixed(2)}</td>
                <td>{formatPrice ? formatPrice(row.high) : row.high.toFixed(2)}</td>
                <td>{formatPrice ? formatPrice(row.low) : row.low.toFixed(2)}</td>
                <td>{formatPrice ? formatPrice(row.close) : row.close.toFixed(2)}</td>
                <td>{Math.round(row.volume)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
