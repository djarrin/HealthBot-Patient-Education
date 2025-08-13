import './App.css';
import './aws-config';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthForm from './components/auth/AuthForm';
import HealthBotChat from './components/HealthBotChat';
import ProtectedRoute from './components/ProtectedRoute';
import RedirectIfAuthenticated from './components/RedirectIfAuthenticated';

console.log('Amplify configured with:', {
  region: process.env.REACT_APP_COGNITO_REGION,
  userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
  clientId: process.env.REACT_APP_COGNITO_CLIENT_ID,
});

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/auth" element={
            <RedirectIfAuthenticated>
              <AuthForm />
            </RedirectIfAuthenticated>
          } />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <HealthBotChat />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/auth" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
