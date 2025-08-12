import './App.css';
import './aws-config';
import AuthForm from './AuthForm';

console.log('Amplify configured with:', {
  region: process.env.REACT_APP_COGNITO_REGION,
  userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
  clientId: process.env.REACT_APP_COGNITO_CLIENT_ID,
});

function App() {
  return (
    <div className="App">
      <AuthForm />
    </div>
  );
}

export default App;
