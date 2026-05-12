import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';

const API_BASE = import.meta.env.VITE_API_URL || '';

function LicenseBanner({ valid, reason }) {
  if (valid) return null;
  return (
    <div className="banner banner-error">
      {reason || 'Your license has expired. Please contact support to renew your license.'}
    </div>
  );
}

function UpdateBanner({ updateAvailable, currentVersion, availableVersion }) {
  if (!updateAvailable) return null;
  return (
    <div className="banner banner-info">
      Update available: version {availableVersion} is ready (current: {currentVersion}).
    </div>
  );
}

function AppContent() {
  const [licenseStatus, setLicenseStatus] = useState({ valid: true });
  const [updateInfo, setUpdateInfo] = useState({ update_available: false });

  useEffect(() => {
    async function fetchLicenseStatus() {
      try {
        const res = await fetch(`${API_BASE}/license/status`);
        if (res.ok) {
          const data = await res.json();
          setLicenseStatus(data);
        }
      } catch (err) {
        console.error('Failed to fetch license status:', err);
      }
    }

    async function fetchUpdateInfo() {
      try {
        const res = await fetch(`${API_BASE}/license/updates`);
        if (res.ok) {
          const data = await res.json();
          setUpdateInfo(data);
        }
      } catch (err) {
        console.error('Failed to fetch update info:', err);
      }
    }

    fetchLicenseStatus();
    fetchUpdateInfo();
  }, []);

  return (
    <>
      <LicenseBanner
        valid={licenseStatus.valid}
        reason={licenseStatus.reason}
      />
      <UpdateBanner
        updateAvailable={updateInfo.update_available}
        currentVersion={updateInfo.current_version}
        availableVersion={updateInfo.available_version}
      />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
