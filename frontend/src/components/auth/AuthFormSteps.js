import { AUTH_STEPS } from './authConstants';
import { AuthInput } from './AuthInput';
import { AuthButton } from './AuthButton';

export const AuthFormSteps = ({ 
  step, 
  email, 
  setEmail, 
  password, 
  setPassword, 
  newPassword, 
  setNewPassword, 
  code, 
  setCode,
  handleSignup,
  handleSignin,
  handleVerify,
  handleForgotPassword,
  handleConfirmResetPassword
}) => {
  const renderSignupSigninInputs = () => (
    <>
      <AuthInput
        type="email"
        placeholder="Email address"
        value={email}
        onChange={e => setEmail(e.target.value)}
      />
      <AuthInput
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
    </>
  );

  const renderVerifyInput = () => (
    <AuthInput
      type="text"
      placeholder="Enter verification code"
      value={code}
      onChange={e => setCode(e.target.value)}
    />
  );

  const renderForgotPasswordInput = () => (
    <AuthInput
      type="email"
      placeholder="Email address"
      value={email}
      onChange={e => setEmail(e.target.value)}
    />
  );

  const renderResetPasswordInputs = () => (
    <>
      <AuthInput
        type="text"
        placeholder="Enter reset code"
        value={code}
        onChange={e => setCode(e.target.value)}
      />
      <AuthInput
        type="password"
        placeholder="New password"
        value={newPassword}
        onChange={e => setNewPassword(e.target.value)}
      />
    </>
  );

  const renderInputs = () => {
    switch (step) {
      case AUTH_STEPS.SIGNUP:
      case AUTH_STEPS.SIGNIN:
        return renderSignupSigninInputs();
      case AUTH_STEPS.VERIFY:
        return renderVerifyInput();
      case AUTH_STEPS.FORGOT_PASSWORD:
        return renderForgotPasswordInput();
      case AUTH_STEPS.RESET_PASSWORD:
        return renderResetPasswordInputs();
      default:
        return null;
    }
  };

  const renderButton = () => {
    switch (step) {
      case AUTH_STEPS.SIGNUP:
        return <AuthButton onClick={handleSignup}>Create Account</AuthButton>;
      case AUTH_STEPS.SIGNIN:
        return <AuthButton onClick={handleSignin}>Sign In</AuthButton>;
      case AUTH_STEPS.VERIFY:
        return <AuthButton onClick={handleVerify}>Verify Email</AuthButton>;
      case AUTH_STEPS.FORGOT_PASSWORD:
        return <AuthButton onClick={handleForgotPassword}>Send Reset Code</AuthButton>;
      case AUTH_STEPS.RESET_PASSWORD:
        return <AuthButton onClick={handleConfirmResetPassword}>Reset Password</AuthButton>;
      default:
        return null;
    }
  };

  return (
    <>
      {renderInputs()}
      {renderButton()}
    </>
  );
};
