import { Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import LiveFeedMonitor from './components/LiveFeedMonitor.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Intersections from './pages/Intersections.jsx';
import EmergencyMode from './pages/EmergencyMode.jsx';
import LandingPage from './pages/LandingPage.jsx';
import LegacyDashboard from './pages/LegacyDashboard.jsx';
import LegacyJunction from './pages/LegacyJunction.jsx';

export default function App() {
  const location = useLocation();
  const isLanding = location.pathname === '/';
  const isLegacyShell = location.pathname === '/legacy' || location.pathname.startsWith('/legacy/junction');

  return (
    <div className="dashboard-shell">
      <div className="absolute inset-0 bg-aurora opacity-80" />
      <div className="relative">
        {!isLanding && <Navbar />}
        <main className={isLanding || isLegacyShell ? "" : "px-6 pb-16 pt-4 sm:px-10"}>
          {!isLanding && !isLegacyShell && (
            <div className="mx-auto mb-6 max-w-7xl">
              <LiveFeedMonitor />
            </div>
          )}
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/intersections" element={<Intersections />} />
            <Route path="/intersections/*" element={<Intersections />} />
            <Route path="/emergency" element={<EmergencyMode />} />
            <Route path="/emergency/*" element={<EmergencyMode />} />
            <Route path="/legacy" element={<LegacyDashboard />} />
            <Route path="/legacy/junction/:jid" element={<LegacyJunction />} />
            <Route path="*" element={<LandingPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
