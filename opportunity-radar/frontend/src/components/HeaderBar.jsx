import React, { useState, useEffect } from 'react';

const HeaderBar = ({ onSearch, onScan, isScanning }) => {
  const [time, setTime] = useState('');
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      }));
    };
    updateTime();
    const intv = setInterval(updateTime, 1000);
    return () => clearInterval(intv);
  }, []);

  const handleSearchClick = () => {
    if (inputValue.trim()) {
      onSearch(inputValue.trim().toUpperCase());
    }
  };

  return (
    <div style={{
      background: 'var(--header)',
      height: 36,
      borderBottom: '1px solid var(--border-header)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      gap: 16,
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Logo */}
      <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: 'var(--amber)', letterSpacing: '0.10em' }}>
        OPPORTUNITY RADAR
      </span>

      {/* Search Input */}
      <div style={{ display: 'flex', alignItems: 'center', background: '#2c2c2c', border: '1px solid #444', height: 28, marginLeft: 24 }}>
        <span style={{ color: '#888', fontSize: 11, padding: '0 8px', fontFamily: 'var(--mono)', flexShrink: 0 }}>
          TICKER
        </span>
        <input 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: '#fff', fontSize: 12, fontFamily: 'var(--mono)', caretColor: 'var(--green)',
            width: 120
          }} 
          placeholder="RELIANCE.NS" 
        />
        <button 
          onClick={handleSearchClick}
          style={{
            background: 'var(--header-muted)', border: 'none', color: '#fff',
            borderLeft: '1px solid #444',
            width: 28, height: 28, cursor: 'pointer', fontSize: 14,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
          ›
        </button>
      </div>

      {/* Scan Button */}
      <button
        onClick={onScan}
        disabled={isScanning}
        style={{
          background: isScanning ? 'var(--header-muted)' : 'var(--green)',
          color: '#fff',
          border: 'none',
          height: 28,
          padding: '0 16px',
          fontFamily: 'var(--mono)',
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: '0.08em',
          cursor: isScanning ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        {isScanning ? (
          <>
            <div className="pulse" style={{ width: 8, height: 8, background: '#fff' }} />
            SCANNING...
          </>
        ) : 'RUN FULL SCAN'}
      </button>

      {/* Live clock */}
      <span style={{ marginLeft: 'auto', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-header-dim)' }}>
        {time} IST
      </span>
    </div>
  );
};

export default HeaderBar;
