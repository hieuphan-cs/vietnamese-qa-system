import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './DashBoard'; 
import ChatUI from './ChatUI';
import Knowledge from './Knowledge'; 
import Admin from './Admin';
import Login from './pages/Login'; 

const ProtectedRoute = ({ children, allowedRoles }) => {
  const isAuthenticated = localStorage.getItem('accessToken');
  const userString = localStorage.getItem('user');
  const user = userString ? JSON.parse(userString) : null;

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  const userRole = user.role ? user.role.toUpperCase() : 'STUDENT';
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    return <Navigate to="/chat" replace />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        >
          <Route path="/chat" element={<ChatUI />} />

          <Route 
            path="/knowledge" 
            element={
              <ProtectedRoute allowedRoles={['TEACHER', 'ADMIN']}>
                <Knowledge />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <Admin />
              </ProtectedRoute>
            }   
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
export default App;