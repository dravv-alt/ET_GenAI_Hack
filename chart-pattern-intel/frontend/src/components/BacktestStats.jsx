export default function BacktestStats({ backtest }) {
  if (!backtest) {
    return (
      <div className="card">
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          BACKTEST
        </div>
        <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>No backtest data available.</div>
      </div>
    );
  }

  const winRate = backtest.win_rate != null ? `${(backtest.win_rate * 100).toFixed(1)}%` : '—';
  const avgGain = backtest.avg_gain_pct != null ? `${backtest.avg_gain_pct.toFixed(2)}%` : '—';
  const avgLoss = backtest.avg_loss_pct != null ? `${backtest.avg_loss_pct.toFixed(2)}%` : '—';
  const medianReturn = backtest.median_return_pct != null ? `${backtest.median_return_pct.toFixed(2)}%` : '—';
  const rrRatio = backtest.rr_ratio != null ? backtest.rr_ratio.toFixed(2) : '—';

  return (
    <div className="card" style={{ display: 'grid', gap: 12 }}>
      <div>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          BACKTEST SUMMARY
        </div>
        <div style={{ fontSize: 20, fontWeight: 600 }}>{backtest.pattern_type.replace('_', ' ')}</div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">SAMPLES</div>
          <div className="value">{backtest.sample_count}</div>
        </div>
        <div className="stat">
          <div className="label">WIN RATE</div>
          <div className="value">{winRate}</div>
        </div>
        <div className="stat">
          <div className="label">MEDIAN RETURN</div>
          <div className="value">{medianReturn}</div>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">AVG GAIN</div>
          <div className="value">{avgGain}</div>
        </div>
        <div className="stat">
          <div className="label">AVG LOSS</div>
          <div className="value">{avgLoss}</div>
        </div>
        <div className="stat">
          <div className="label">R/R RATIO</div>
          <div className="value">{rrRatio}</div>
        </div>
      </div>
      <div>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-muted)' }}>
          NOTE
        </div>
        <div style={{ marginTop: 6 }}>{backtest.note}</div>
      </div>
    </div>
  );
}
