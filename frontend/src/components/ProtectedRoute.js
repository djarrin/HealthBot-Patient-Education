import { useState, useEffect } from 'react';
import { getCurrentUser } from 'aws-amplify/auth';
import { Navigate } from 'react-router-dom';
import LoadingSpinner from './LoadingSpinner';

export default function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      await getCurrentUser();
      setIsAuthenticated(true);
    } catch (error) {
      console.log('No authenticated user found');
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return isAuthenticated ? children : <Navigate to="/auth" replace />;
}
