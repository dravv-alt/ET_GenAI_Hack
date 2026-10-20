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
  const maxDrawdown = backtest.max_drawdown_pct != null ? `${backtest.max_drawdown_pct.toFixed(2)}%` : '—';
  const calmar = backtest.calmar_ratio != null ? backtest.calmar_ratio.toFixed(2) : '—';
  const sharpe = backtest.sharpe_ratio != null ? backtest.sharpe_ratio.toFixed(2) : '—';
  const sortino = backtest.sortino_ratio != null ? backtest.sortino_ratio.toFixed(2) : '—';
  const profitFactor = backtest.profit_factor != null ? backtest.profit_factor.toFixed(2) : '—';
  const expectancy = backtest.expectancy != null ? backtest.expectancy.toFixed(3) : '—';
  const exposure = backtest.exposure_pct != null ? `${backtest.exposure_pct.toFixed(1)}%` : '—';
  const avgBarsHeld = backtest.avg_time_in_trade_bars != null ? backtest.avg_time_in_trade_bars.toFixed(1) : '—';
  const avgBarsTarget = backtest.avg_bars_to_target != null ? backtest.avg_bars_to_target.toFixed(1) : '—';
  const avgBarsStop = backtest.avg_bars_to_stop != null ? backtest.avg_bars_to_stop.toFixed(1) : '—';

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
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">MAX DRAWDOWN</div>
          <div className="value">{maxDrawdown}</div>
        </div>
        <div className="stat">
          <div className="label">CALMAR</div>
          <div className="value">{calmar}</div>
        </div>
        <div className="stat">
          <div className="label">EXPOSURE</div>
          <div className="value">{exposure}</div>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">SHARPE</div>
          <div className="value">{sharpe}</div>
        </div>
        <div className="stat">
          <div className="label">SORTINO</div>
          <div className="value">{sortino}</div>
        </div>
        <div className="stat">
          <div className="label">PROFIT FACTOR</div>
          <div className="value">{profitFactor}</div>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">EXPECTANCY</div>
          <div className="value">{expectancy}</div>
        </div>
        <div className="stat">
          <div className="label">AVG BARS HELD</div>
          <div className="value">{avgBarsHeld}</div>
        </div>
        <div className="stat">
          <div className="label">BARS TO TARGET</div>
          <div className="value">{avgBarsTarget}</div>
        </div>
      </div>
      <div className="grid" style={{ gridTemplateColumns: 'repeat(1, 1fr)', gap: 12 }}>
        <div className="stat">
          <div className="label">BARS TO STOP</div>
          <div className="value">{avgBarsStop}</div>
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
