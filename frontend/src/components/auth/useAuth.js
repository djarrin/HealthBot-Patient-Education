import { useState } from 'react';
import {
    signUp,
    confirmSignUp,
    signIn,
    resetPassword,
    confirmResetPassword,
} from 'aws-amplify/auth';
import { AUTH_STEPS, MESSAGE_TYPES } from './authConstants';

export const useAuth = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [step, setStep] = useState(AUTH_STEPS.SIGNUP);
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const showMessage = (text, type = MESSAGE_TYPES.SUCCESS) => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => setMessage(''), 5000);
  };

  const handleSignup = async () => {
    try {
      await signUp({ username: email, password });
      showMessage('Check your email for a verification code.', MESSAGE_TYPES.INFO);
      setStep(AUTH_STEPS.VERIFY);
    } catch (err) {
      console.error('Signup error', err);
      showMessage(err.message, MESSAGE_TYPES.ERROR);
    }
  };

  const handleVerify = async () => {
    try {
      await confirmSignUp({ username: email, confirmationCode: code });
      showMessage('Email verified. You can now sign in.', MESSAGE_TYPES.SUCCESS);
      setStep(AUTH_STEPS.SIGNIN);
    } catch (err) {
      console.error('Verification error', err);
      showMessage(err.message, MESSAGE_TYPES.ERROR);
    }
  };

  const handleSignin = async () => {
    try {
      const user = await signIn({ username: email, password });
      showMessage('Login successful!', MESSAGE_TYPES.SUCCESS);
      console.log('Signed in user:', user);
    } catch (err) {
      console.error('Signin error', err);
      showMessage(err.message, MESSAGE_TYPES.ERROR);
    }
  };

  const handleForgotPassword = async () => {
    try {
      await resetPassword({ username: email });
      showMessage('Check your email for a password reset code.', MESSAGE_TYPES.INFO);
      setStep(AUTH_STEPS.RESET_PASSWORD);
    } catch (err) {
      console.error('Reset password error', err);
      showMessage(err.message, MESSAGE_TYPES.ERROR);
    }
  };

  const handleConfirmResetPassword = async () => {
    try {
      await confirmResetPassword({ 
        username: email, 
        confirmationCode: code, 
        newPassword 
      });
      showMessage('Password reset successful! You can now sign in.', MESSAGE_TYPES.SUCCESS);
      setStep(AUTH_STEPS.SIGNIN);
      setNewPassword('');
    } catch (err) {
      console.error('Confirm reset password error', err);
      showMessage(err.message, MESSAGE_TYPES.ERROR);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setNewPassword('');
    setCode('');
    setMessage('');
    setMessageType('');
  };

  return {
    // State
    email,
    setEmail,
    password,
    setPassword,
    newPassword,
    setNewPassword,
    step,
    setStep,
    code,
    setCode,
    message,
    messageType,
    
    // Actions
    handleSignup,
    handleVerify,
    handleSignin,
    handleForgotPassword,
    handleConfirmResetPassword,
    showMessage,
    resetForm,
  };
};