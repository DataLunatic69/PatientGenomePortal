import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PageShell from './components/layout/PageShell';
import UploadPage from './pages/UploadPage';
import ProgressPage from './pages/ProgressPage';
import DashboardPage from './pages/DashboardPage';
import VariantDetailPage from './pages/VariantDetailPage';
import AuthPage from './pages/AuthPage';
import LandingPage from './pages/LandingPage';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (token: string, user: any) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return <div className="flex h-screen w-screen items-center justify-center">Loading...</div>;
  }

  return (
    <BrowserRouter>
      {isAuthenticated ? (
        <PageShell onLogout={handleLogout}>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/progress/:jobId" element={<ProgressPage />} />
            <Route path="/dashboard/:jobId" element={<DashboardPage />} />
            <Route path="/variant/:variantId" element={<VariantDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PageShell>
      ) : (
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}

export default App;
