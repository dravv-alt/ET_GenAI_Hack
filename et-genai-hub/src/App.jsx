import { useState } from 'react';
import './index.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('CHATGPT');

  const tabs = [
    { id: 'CHATGPT', label: 'MARKET GPT & TERMINAL', url: 'http://localhost:3003' },
    { id: 'RADAR', label: 'OPPORTUNITY RADAR', url: 'http://localhost:3001' },
    { id: 'PATTERNS', label: 'CHART INTEL', url: 'http://localhost:3002' },
    { id: 'VIDEO', label: 'AI VIDEO ENGINE', url: 'http://localhost:3004' },
  ];

  const activeUrl = tabs.find(t => t.id === activeTab)?.url;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden', background: '#000' }}>
      <div style={{
        background: '#1e1e1e', // Dark header background
        height: 40,
        flexShrink: 0,
        borderBottom: '1px solid #333',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 24,
      }}>
        <span style={{ fontFamily: 'monospace', fontSize: 14, fontWeight: 700, color: '#fff', letterSpacing: '0.10em' }}>
          ET AI TERMINAL HUB
        </span>
        
        <div style={{ display: 'flex', gap: 4, height: '100%' }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                background: activeTab === t.id ? '#333' : 'transparent',
                border: 'none',
                borderTop: activeTab === t.id ? '2px solid #00ff00' : '2px solid transparent',
                color: activeTab === t.id ? '#fff' : '#aaa',
                fontFamily: 'monospace',
                fontSize: 12,
                fontWeight: activeTab === t.id ? 600 : 400,
                padding: '0 16px',
                cursor: 'pointer',
                height: '100%',
                transition: 'all 0.1s'
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
        <span style={{ marginLeft: 'auto', fontFamily: 'monospace', fontSize: 11, color: '#aaa', letterSpacing: '0.05em' }}>
          IFRAME SHELL • PORTS 3001-3004
        </span>
      </div>

      <div style={{ flex: 1, overflow: 'hidden' }}>
        <iframe
          src={activeUrl}
          style={{ width: '100%', height: '100%', border: 'none' }}
          title={`${activeTab} Frame`}
        />
      </div>
    </div>
  );
}
