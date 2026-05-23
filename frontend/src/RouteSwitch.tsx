import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

/**
 * ROUTE MANAGER - Gère la navigation entre pages
 * 
 * Routes:
 * - /                → Landing page (accueil)
 * - /app            → Application principale (App.tsx)
 * - /admin          → Admin panel
 * - /login          → Page login
 * - Autres          → Redirect vers landing
 */

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import App from './App';

interface RouteConfig {
  path: string;
  label: string;
  component: React.ComponentType;
  public: boolean;
}

export const routes: RouteConfig[] = [
  {
    path: '/',
    label: 'Accueil',
    component: Landing,
    public: true
  },
  {
    path: '/app',
    label: 'Application',
    component: App,
    public: false
  }
];

export const RouteSwitch: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC ROUTES */}
        <Route path="/" element={<Landing />} />
        <Route path="/auth/login/" element={<Login />} />
        <Route path="/auth/register/" element={<Register />} />
        
        {/* PROTECTED ROUTES */}
        <Route path="/app/*" element={<App />} />
        
        {/* DEFAULT REDIRECT */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default RouteSwitch;
