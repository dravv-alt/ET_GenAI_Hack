import { useEffect, useRef } from 'react';
import { createChart, CrosshairMode } from 'lightweight-charts';

const BEARISH_TYPES = new Set(['double_top', 'head_shoulders']);
const PATTERN_FAMILIES = {
  breakout: 'breakout',
  rsi_divergence: 'momentum',
  macd_crossover: 'momentum',
  golden_cross: 'momentum',
  double_bottom: 'reversal',
  double_top: 'reversal',
  head_shoulders: 'reversal',
  hammer: 'candlestick',
  engulfing: 'candlestick',
};
const FAMILY_STYLES = {
  breakout: { color: '#16a34a', shape: 'arrowUp' },
  momentum: { color: '#d97706', shape: 'circle' },
  reversal: { color: '#dc2626', shape: 'circle' },
  candlestick: { color: '#2563eb', shape: 'square' },
  other: { color: '#64748b', shape: 'circle' },
};

const formatDate = (value) => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toISOString().slice(0, 10);
};

const shiftDate = (value, deltaDays) => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  parsed.setUTCDate(parsed.getUTCDate() + deltaDays);
  return parsed.toISOString().slice(0, 10);
};

const resolveFamily = (patternType) => PATTERN_FAMILIES[patternType] || 'other';

export default function CandlestickChart({
  ohlcv = [],
  levels = [],
  patterns = [],
  selected,
  onSelectPattern,
  height = 240,
  formatPrice,
}) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const priceLinesRef = useRef([]);
  const tradeLinesRef = useRef([]);
  const riskSeriesRef = useRef(null);
  const rewardSeriesRef = useRef(null);

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
    const riskSeries = chart.addAreaSeries({
      lineWidth: 0,
      priceLineVisible: false,
      topColor: 'rgba(220, 38, 38, 0.18)',
      bottomColor: 'rgba(220, 38, 38, 0.04)',
    });
    const rewardSeries = chart.addAreaSeries({
      lineWidth: 0,
      priceLineVisible: false,
      topColor: 'rgba(22, 163, 74, 0.18)',
      bottomColor: 'rgba(22, 163, 74, 0.04)',
    });

    chartRef.current = chart;
    seriesRef.current = series;
    riskSeriesRef.current = riskSeries;
    rewardSeriesRef.current = rewardSeries;

    const ro = new ResizeObserver(() => {
      chart.applyOptions({ width: containerRef.current?.clientWidth || 600 });
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [height]);

  const toChartTime = (value) => {
    if (!value) return null;
    if (typeof value === 'string' && value.includes(' ')) {
      const parsed = new Date(value.replace(' ', 'T'));
      if (Number.isNaN(parsed.getTime())) return null;
      return Math.floor(parsed.getTime() / 1000);
    }
    return value;
  };

  useEffect(() => {
    if (!seriesRef.current) return;
    const data = ohlcv
      .map((row) => ({
        time: toChartTime(row.date),
        open: row.open,
        high: row.high,
        low: row.low,
        close: row.close,
      }))
      .filter((row) => row.time != null);
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
        const bearish = BEARISH_TYPES.has(pattern.pattern_type);
        const family = resolveFamily(pattern.pattern_type);
        const style = FAMILY_STYLES[family] || FAMILY_STYLES.other;
        return {
          time: toChartTime(pattern.detected_on),
          position: bearish ? 'aboveBar' : 'belowBar',
          color: style.color,
          shape: bearish ? 'arrowDown' : style.shape,
          text: pattern.pattern_type.replace('_', ' '),
        };
      })
      .filter((row) => row.time != null);
    seriesRef.current.setMarkers(markers);
  }, [patterns]);

  useEffect(() => {
    if (!seriesRef.current || !riskSeriesRef.current || !rewardSeriesRef.current) return;

    tradeLinesRef.current.forEach((line) => {
      try {
        seriesRef.current.removePriceLine(line);
      } catch {
        // ignore if line is already removed
      }
    });
    tradeLinesRef.current = [];
    riskSeriesRef.current.setData([]);
    rewardSeriesRef.current.setData([]);

    if (!selected || !ohlcv.length) return;
    const entry = Number(selected.entry_price);
    const stop = Number(selected.stop_loss);
    const target = Number(selected.target_price);
    if (!Number.isFinite(entry) || !Number.isFinite(stop) || !Number.isFinite(target)) return;

    const times = ohlcv.map((row) => toChartTime(row.date)).filter((time) => time != null);
    const riskLow = Math.min(entry, stop);
    const riskHigh = Math.max(entry, stop);
    const rewardLow = Math.min(entry, target);
    const rewardHigh = Math.max(entry, target);

    riskSeriesRef.current.applyOptions({
      baseValue: { type: 'price', price: riskLow },
    });
    riskSeriesRef.current.setData(times.map((time) => ({ time, value: riskHigh })));

    rewardSeriesRef.current.applyOptions({
      baseValue: { type: 'price', price: rewardLow },
    });
    rewardSeriesRef.current.setData(times.map((time) => ({ time, value: rewardHigh })));

    tradeLinesRef.current.push(
      seriesRef.current.createPriceLine({
        price: entry,
        color: '#d97706',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
      }),
      seriesRef.current.createPriceLine({
        price: stop,
        color: '#dc2626',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
      }),
      seriesRef.current.createPriceLine({
        price: target,
        color: '#16a34a',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
      })
    );
  }, [ohlcv, selected]);

  const timelineEvents = patterns
    .filter((pattern) => pattern.detected_on)
    .slice()
    .sort((a, b) => new Date(a.detected_on) - new Date(b.detected_on));

  const focusOnTime = (time) => {
    if (!chartRef.current || !time) return;
    const from = shiftDate(time, -20);
    const to = shiftDate(time, 20);
    chartRef.current.timeScale().setVisibleRange({ from, to });
  };

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
      {timelineEvents.length > 0 && (
        <div className="event-rail">
          <div className="event-rail-title">EVENTS</div>
          <div className="event-rail-track">
            {timelineEvents.map((pattern, idx) => {
              const family = resolveFamily(pattern.pattern_type);
              const isActive = selected?.pattern_type === pattern.pattern_type;
              return (
                <button
                  key={`${pattern.pattern_type}-${pattern.detected_on}-${idx}`}
                  type="button"
                  className={`event-dot event-${family} ${isActive ? 'active' : ''}`}
                  title={`${formatDate(pattern.detected_on)} • ${pattern.pattern_type.replace('_', ' ')}`}
                  onClick={() => {
                    onSelectPattern?.(pattern);
                    focusOnTime(pattern.detected_on);
                  }}
                />
              );
            })}
          </div>
        </div>
      )}
      {!ohlcv.length && (
        <div className="chart-empty">AWAITING DATA</div>
      )}
      {ohlcv.length > 0 && (
        <div className="table-scroll">
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
        </div>
      )}
    </div>
  );
}
