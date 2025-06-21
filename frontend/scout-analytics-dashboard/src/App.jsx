import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { GlobalFilterBar } from './components/GlobalFilterBar';
import { Overview } from './pages/Overview';
import { TransactionTrends } from './pages/TransactionTrends';
import ProductMix from './pages/ProductMix';
import ConsumerInsights from './pages/ConsumerInsights';
import { RetailBotInsights } from './pages/RetailBotInsights';
import { useFilterStore } from './stores/filterStore';
import './App.css';

function AppContent() {
  const location = useLocation();
  const setFromQueryString = useFilterStore((state) => state.setFromQueryString);

  useEffect(() => {
    // Initialize filters from URL on page load
    setFromQueryString(location.search);
  }, [location.search, setFromQueryString]);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {location.pathname !== '/retailbot' && <GlobalFilterBar />}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/trends" element={<TransactionTrends />} />
            <Route path="/products" element={<ProductMix />} />
            <Route path="/insights" element={<ConsumerInsights />} />
            <Route path="/retailbot" element={<RetailBotInsights />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

