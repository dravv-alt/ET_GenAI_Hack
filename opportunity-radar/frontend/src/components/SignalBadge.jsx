import React from 'react';
import { signalBg, signalColor, getDirection } from '../utils/theme';

const SignalBadge = ({ type, name, small }) => {
  const dir = getDirection(type);
  const color = signalColor(type);
  const bg = signalBg(type);
  
  return (
    <span style={{
      display: 'inline-block',
      fontSize: small ? 10 : 11,
      fontFamily: 'var(--mono)',
      fontWeight: 500,
      color: color,
      background: bg,
      border: `1px solid ${color}`,
      padding: small ? '1px 5px' : '2px 7px',
      letterSpacing: '0.03em',
      whiteSpace: 'nowrap',
    }}>
      {dir === 'bullish' ? '▲' : dir === 'bearish' ? '▼' : '◆'} {name}
    </span>
  );
};

export default SignalBadge;
