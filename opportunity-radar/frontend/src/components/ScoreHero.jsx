import React from 'react';
import { scoreColor } from '../utils/theme';

const ScoreHero = ({ score, label }) => {
  const safeScore = Math.round(score || 0);
  const color = scoreColor(safeScore);
  
  return (
    <div style={{ textAlign: 'center', padding: '16px 14px 14px', borderBottom: '1px solid var(--border)' }}>
      <div style={{ 
        fontFamily: 'var(--mono)', 
        fontSize: 52, 
        fontWeight: 600, 
        color: color, 
        lineHeight: 1, 
        letterSpacing: '-0.04em' 
      }}>
        {safeScore}
      </div>
      <div style={{ 
        fontFamily: 'var(--mono)', 
        fontSize: 10, 
        color: 'var(--text-muted)', 
        marginTop: 4, 
        letterSpacing: '0.10em' 
      }}>
        / 100
      </div>
      <div style={{
        marginTop: 8, 
        display: 'inline-block', 
        padding: '2px 10px',
        background: color, 
        color: '#fff',
        fontFamily: 'var(--mono)', 
        fontSize: 10, 
        fontWeight: 600, 
        letterSpacing: '0.08em',
      }}>
        {(label || 'CONFIDENCE').toUpperCase()}
      </div>
    </div>
  );
};

export default ScoreHero;
