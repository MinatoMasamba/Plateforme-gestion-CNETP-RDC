import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import App from './App';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import PublicNorms from './pages/PublicNorms';
import PublicNormDetail from './pages/PublicNormDetail';
import './index.css';

function LoadingScreen() {
  return (
    <div className="h-screen w-screen bg-[#020204] flex items-center justify-center">
      <div className="text-emerald-400 text-sm animate-pulse">
        Vérification de l'authentification...
      </div>
    </div>
  );
}

function IndexRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Landing />;
  }

  if (isAuthenticated && user?.is_expert) {
    return <Navigate to="/app/" replace />;
  }

  if (isAuthenticated && !user?.is_expert) {
    return <Navigate to="/public/norms/" replace />;
  }

  return <Navigate to="/auth/login/" replace />; // Fallback
}

function Root() {
  const { isAuthenticated, user } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<IndexRoute />} />
        <Route path="/auth/login/" element={<Login />} />
        <Route path="/auth/register/" element={<Register />} />
        <Route path="/public/norms/" element={<PublicNorms />} />
        <Route path="/public/norms/:id/" element={<PublicNormDetail />} />

        <Route
          path="/app/*"
          element={
            isAuthenticated && user?.is_expert ? <App /> : <Navigate to={isAuthenticated ? "/public/norms/" : "/auth/login/"} replace />
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <Root />
    </AuthProvider>
  </StrictMode>
);
