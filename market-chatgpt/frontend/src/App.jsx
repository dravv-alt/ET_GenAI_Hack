import { useState } from 'react';
import { MarketDashboard } from './components/MarketDashboard';
import { ChatWindow } from './components/ChatWindow';
import { PortfolioUploader } from './components/PortfolioUploader';
import { TopIndexBar } from './components/TopIndexBar';

function App() {
  const [marketContext, setMarketContext] = useState([]);
  const [portfolioData, setPortfolioData] = useState(null);
  
  // Header component following Bloomberg Spec
  const Header = () => (
    <div style={{
      background: 'var(--header)',
      height: 36,
      borderBottom: '1px solid var(--border-header)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      gap: 16,
    }}>
      <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: '#fff', letterSpacing: '0.10em' }}>
        MARKET CHATGPT NEXT GEN
      </span>
      <span style={{ marginLeft: 'auto', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-header-dim)' }}>
        ET AI HACKATHON
      </span>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header />
      <TopIndexBar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* Left/Main Panel: Live Dashboard */}
        <div style={{ width: '45%', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', background: 'var(--bg-white)', transition: 'width 0.2s' }}>
          
          <PortfolioUploader data={portfolioData} onDataParsed={setPortfolioData} />
          <div style={{
            padding: '6px 12px',
            background: 'var(--header-sub)',
            borderBottom: '1px solid var(--border-header)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#aaa', letterSpacing: '0.10em' }}>
              LIVE MARKET DASHBOARD (NIFTY 100)
            </span>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--green)' }}>
              CONNECTED
            </span>
          </div>
          <div style={{ flex: 1, overflowY: 'hidden' }}>
            <MarketDashboard onContextChange={setMarketContext} />
          </div>
        </div>

        {/* Right Panel: Chat Stream (Bloomberg Chat Spec) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
          <div style={{
            padding: '6px 12px',
            background: 'var(--header-sub)',
            borderBottom: '1px solid var(--border-header)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#aaa', letterSpacing: '0.10em' }}>
              AGENTS: OMNISCIENT TERMINAL
            </span>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#aaa' }}>
              CONTEXT: {marketContext.length} TICKERS
            </span>
          </div>
          <ChatWindow portfolio={portfolioData ? portfolioData.holdings : []} marketContext={marketContext} />
        </div>
        
      </div>
    </div>
  );
}

export default App;
