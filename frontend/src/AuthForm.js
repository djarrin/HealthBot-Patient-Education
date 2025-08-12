import { useState } from 'react';
import {
    signUp,
    confirmSignUp,
    signIn,
} from 'aws-amplify/auth';

export default function AuthForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep] = useState('signup'); 
  const [code, setCode] = useState('');

  const handleSignup = async () => {
    try {
      await signUp({ username: email, password });
      alert('Check your email for a verification code.');
      setStep('verify');
    } catch (err) {
      console.error('Signup error', err);
      alert(err.message);
    }
  };
  
  const handleVerify = async () => {
    try {
      await confirmSignUp({ username: email, confirmationCode: code });
      alert('Email verified. You can now sign in.');
      setStep('signin');
    } catch (err) {
      console.error('Verification error', err);
      alert(err.message);
    }
  };
  
  const handleSignin = async () => {
    try {
      const user = await signIn({ username: email, password });
      alert('Login successful!');
      console.log('Signed in user:', user);
    } catch (err) {
      console.error('Signin error', err);
      alert(err.message);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 400 }}>
      <h2>{step === 'signup' ? 'Create Account' : step === 'signin' ? 'Login' : 'Verify Email'}</h2>

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        style={{ display: 'block', marginBottom: 8 }}
      />
      {step !== 'verify' && (
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ display: 'block', marginBottom: 8 }}
        />
      )}

      {step === 'signup' && <button onClick={handleSignup}>Sign Up</button>}
      {step === 'signin' && <button onClick={handleSignin}>Sign In</button>}
      {step === 'verify' && (
        <>
          <input
            type="text"
            placeholder="Verification Code"
            value={code}
            onChange={e => setCode(e.target.value)}
            style={{ display: 'block', marginBottom: 8 }}
          />
          <button onClick={handleVerify}>Confirm</button>
        </>
      )}

      <p style={{ marginTop: 12 }}>
        {step !== 'signin' && <button onClick={() => setStep('signin')}>Go to Login</button>}
        {step !== 'signup' && <button onClick={() => setStep('signup')}>Go to Sign Up</button>}
      </p>
    </div>
  );
}