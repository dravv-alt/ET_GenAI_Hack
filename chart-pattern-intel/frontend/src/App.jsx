import React, { useEffect, useMemo, useState } from 'react';
import TickerSearch from './components/TickerSearch.jsx';
import CandlestickChart from './components/CandlestickChart.jsx';
import PatternCard from './components/PatternCard.jsx';
import BacktestStats from './components/BacktestStats.jsx';
import ExplanationPanel from './components/ExplanationPanel.jsx';
import LevelMarkers from './components/LevelMarkers.jsx';
import PatternOverlay from './components/PatternOverlay.jsx';
import ScorePanel from './components/ScorePanel.jsx';
import { fetchBacktest, fetchChart, fetchPatterns, fetchScan } from './lib/api.js';
import { TICKERS } from './lib/tickers.js';
import { fmtDate, fmtPct, fmtPrice, fmtTime } from './lib/formatters.js';

const DEFAULT_TICKER = 'RELIANCE';

export default function App() {
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [chart, setChart] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [levels, setLevels] = useState([]);
  const [selected, setSelected] = useState(null);
  const [backtest, setBacktest] = useState(null);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [time, setTime] = useState(fmtTime());
  const [showBacktest, setShowBacktest] = useState(false);
  const [period, setPeriod] = useState('1y');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [scanStatus, setScanStatus] = useState('idle');
  const [scanResults, setScanResults] = useState([]);
  const [scanError, setScanError] = useState('');
  const [refreshTick, setRefreshTick] = useState(0);

  const tickers = useMemo(() => TICKERS, []);

  useEffect(() => {
    const id = setInterval(() => setTime(fmtTime()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(() => {
      setRefreshTick((tick) => tick + 1);
    }, 60000);
    return () => clearInterval(id);
  }, [autoRefresh]);

  useEffect(() => {
    let active = true;
    async function load() {
      setStatus('loading');
      setError('');
      try {
        const [chartResp, patternResp] = await Promise.all([
          fetchChart(ticker, period),
          fetchPatterns(ticker, period),
        ]);
        if (!active) return;
        setChart(chartResp);
        setPatterns(patternResp.patterns || []);
        setLevels(patternResp.levels || []);
        setSelected(patternResp.patterns?.[0] || null);
        setStatus('ready');
      } catch (err) {
        if (!active) return;
        setStatus('error');
        setError(err.message || 'Failed to load data');
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [ticker, period, refreshTick]);

  const runScan = async () => {
    setScanStatus('loading');
    setScanError('');
    try {
      const tickersList = tickers.map((item) => item.symbol);
      const resp = await fetchScan(tickersList, period, 25);
      setScanResults(resp.results || []);
      setScanStatus('ready');
    } catch (err) {
      setScanStatus('error');
      setScanError(err.message || 'Scan failed');
    }
  };

  useEffect(() => {
    let active = true;
    async function loadBacktest() {
      if (!selected) {
        setBacktest(null);
        return;
      }
      try {
        const resp = await fetchBacktest(ticker, selected.pattern_type);
        if (!active) return;
        setBacktest(resp);
        setShowBacktest(false);
      } catch (err) {
        if (!active) return;
        setBacktest({
          pattern_type: selected.pattern_type,
          sample_count: 0,
          note: err.message || 'Backtest unavailable',
        });
      }
    }
    loadBacktest();
    return () => {
      active = false;
    };
  }, [ticker, selected]);

  const explanation = useMemo(() => {
    if (!selected) return '';
    const detail = selected.plain_english || selected.description || '';
    const backtestNote = backtest?.note ? ` ${backtest.note}` : '';
    return `${detail}${backtestNote}`.trim();
  }, [selected, backtest]);

  const marketSnapshot = useMemo(() => {
    const rows = chart?.ohlcv || [];
    if (rows.length === 0) return null;
    const last = rows[rows.length - 1];
    const prev = rows.length > 1 ? rows[rows.length - 2] : null;
    const change = prev ? (last.close - prev.close) / prev.close : null;
    return {
      last,
      change,
    };
  }, [chart]);

  const backtestSpark = useMemo(() => {
    if (!backtest) return null;
    const winRate = backtest.win_rate ?? null;
    const avgGain = backtest.avg_gain_pct ?? null;
    const avgLoss = backtest.avg_loss_pct ?? null;
    if (winRate == null && avgGain == null && avgLoss == null) return null;
    const gain = avgGain != null ? Math.min(Math.abs(avgGain) / 5, 1) : 0;
    const loss = avgLoss != null ? Math.min(Math.abs(avgLoss) / 5, 1) : 0;
    return {
      win: winRate != null ? Math.min(Math.max(winRate, 0), 1) : 0,
      gain,
      loss,
    };
  }, [backtest]);

  return (
    <div className="app-root">
      <div className="topbar">
        <div className="topbar-title">CHART PATTERN INTEL</div>
        <TickerSearch
          value={ticker}
          tickers={tickers}
          onSelect={setTicker}
        />
        <button
          type="button"
          className={`topbar-button ${autoRefresh ? 'active' : ''}`}
          onClick={() => setAutoRefresh((prev) => !prev)}
        >
          AUTO REFRESH {autoRefresh ? 'ON' : 'OFF'}
        </button>
        <div className="status-pill">
          <span className="status-dot" />
          NSE LIVE
        </div>
        <div className="topbar-clock">{time}</div>
      </div>

      <div className="layout">
        <aside className="panel">
          <div className="section-cap">
            <span>ALERT FEED</span>
            <span className="mono" style={{ color: 'var(--green)' }}>
              {patterns.length}
            </span>
          </div>
          <div className="panel-actions">
            <button
              type="button"
              className="panel-button"
              onClick={runScan}
              disabled={scanStatus === 'loading'}
            >
              {scanStatus === 'loading' ? 'SCANNING...' : 'SCAN NIFTY 50'}
            </button>
            {scanStatus === 'error' && <span className="panel-error">{scanError}</span>}
          </div>
          <div style={{ padding: 12, display: 'grid', gap: 8 }}>
            {patterns.length === 0 && status === 'ready' && (
              <div className="tag">NO STRONG PATTERNS</div>
            )}
            {patterns.map((pattern) => (
              <PatternCard
                key={`${pattern.pattern_type}-${pattern.detected_on}`}
                pattern={pattern}
                active={selected?.pattern_type === pattern.pattern_type}
                onSelect={setSelected}
              />
            ))}
          </div>
          <div className="scan-results">
            <div className="scan-header">SCAN RESULTS</div>
            {scanStatus === 'loading' && <div className="tag">RUNNING SCAN</div>}
            {scanStatus === 'ready' && scanResults.length === 0 && (
              <div className="tag">NO RESULTS</div>
            )}
            {scanResults.map((item) => (
              <button
                key={`${item.ticker}-${item.pattern?.pattern_type}`}
                type="button"
                className="scan-item"
                onClick={() => setTicker(item.ticker.replace('.NS', ''))}
              >
                <div className="scan-symbol">{item.ticker.replace('.NS', '')}</div>
                <div className="scan-pattern">{item.pattern?.pattern_type?.replace('_', ' ')}</div>
                <div className="scan-score">{item.rank_score != null ? item.rank_score.toFixed(2) : '—'}</div>
              </button>
            ))}
          </div>
        </aside>

        <main className="panel">
          <div className="section-cap">
            <span>CHART VIEW</span>
            <span className="mono" style={{ color: 'var(--text-header-dim)' }}>
              {ticker}
            </span>
          </div>
          <div className="chart-header">
            <div>
              <div className="chart-title">{ticker}</div>
              <div className="chart-sub">LAST UPDATE {marketSnapshot ? fmtDate(marketSnapshot.last.date) : '-'}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
              <div className="chart-price">
                {marketSnapshot ? fmtPrice(marketSnapshot.last.close) : '-'}
              </div>
              <div className={`chart-change ${marketSnapshot?.change >= 0 ? 'up' : 'down'}`}>
                {marketSnapshot ? fmtPct(marketSnapshot.change) : '-'}
              </div>
              <div className="period-select">
                <span className="mono">PERIOD</span>
                <select value={period} onChange={(event) => setPeriod(event.target.value)}>
                  <option value="6mo">6M</option>
                  <option value="1y">1Y</option>
                  <option value="2y">2Y</option>
                  <option value="5y">5Y</option>
                </select>
              </div>
            </div>
          </div>
          <div style={{ padding: 12, display: 'grid', gap: 12 }}>
            {status === 'loading' && <div className="tag">FETCHING LATEST DATA</div>}
            {status === 'error' && <div className="tag">{error}</div>}
            {status === 'ready' && patterns.length === 0 && (
              <div className="card" style={{ display: 'grid', gap: 6 }}>
                <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
                  NO PATTERNS
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Try a longer period or another ticker to surface stronger signals.
                </div>
              </div>
            )}
            {chart && (
              <CandlestickChart ohlcv={chart.ohlcv} levels={levels} patterns={patterns} />
            )}
            {patterns.length > 0 && (
              <div className="pattern-strip">
                <span className="mono">DETECTED</span>
                {patterns.map((pattern) => (
                  <span
                    key={`${pattern.pattern_type}-${pattern.detected_on}`}
                    className={`pill ${['double_top', 'head_shoulders'].includes(pattern.pattern_type) ? 'pill-negative' : 'pill-positive'}`}
                  >
                    {pattern.pattern_type.replace('_', ' ')}
                  </span>
                ))}
              </div>
            )}
            <div className="backtest-toggle">
              <div>
                <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
                  BACKTEST
                </div>
                <div style={{ fontWeight: 600 }}>{selected ? selected.pattern_type.replace('_', ' ') : 'NO PATTERN'}</div>
              </div>
              {backtestSpark && (
                <div className="backtest-sparkline" aria-hidden="true">
                  <span style={{ height: `${Math.round(backtestSpark.win * 100)}%` }} />
                  <span className="gain" style={{ height: `${Math.round(backtestSpark.gain * 100)}%` }} />
                  <span className="loss" style={{ height: `${Math.round(backtestSpark.loss * 100)}%` }} />
                </div>
              )}
              <button
                type="button"
                className="backtest-button"
                onClick={() => setShowBacktest((prev) => !prev)}
                disabled={!selected}
              >
                {showBacktest ? 'HIDE' : 'VIEW'}
              </button>
            </div>
            {showBacktest && <BacktestStats backtest={backtest} />}
            <PatternOverlay patterns={patterns} />
            <LevelMarkers levels={levels} />
            <ExplanationPanel explanation={explanation} />
          </div>
        </main>

        <aside className="panel panel-right">
          <div className="section-cap">
            <span>SCORE PANEL</span>
            <span className="mono" style={{ color: 'var(--amber)' }}>
              {selected?.pattern_type || 'NONE'}
            </span>
          </div>
          <div style={{ padding: 12, display: 'grid', gap: 12 }}>
            <ScorePanel patterns={patterns} selected={selected} backtest={backtest} />
          </div>
        </aside>
      </div>
    </div>
  );
}
