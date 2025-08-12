import { STEP_TITLES } from './authConstants';
import { useAuth } from './useAuth';
import { AuthMessage } from './AuthMessage';
import { AuthFormSteps } from './AuthFormSteps';
import { AuthNavigation } from './AuthNavigation';
import '../../assets/login-flow.css';

export default function AuthForm() {
  const {
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
    handleSignup,
    handleVerify,
    handleSignin,
    handleForgotPassword,
    handleConfirmResetPassword,
  } = useAuth();

  return (
    <div className="auth-container">
      <div className="auth-form-card">
        <h2 className="auth-title">{STEP_TITLES[step]}</h2>

        <AuthMessage message={message} messageType={messageType} />

        <AuthFormSteps
          step={step}
          email={email}
          setEmail={setEmail}
          password={password}
          setPassword={setPassword}
          newPassword={newPassword}
          setNewPassword={setNewPassword}
          code={code}
          setCode={setCode}
          handleSignup={handleSignup}
          handleSignin={handleSignin}
          handleVerify={handleVerify}
          handleForgotPassword={handleForgotPassword}
          handleConfirmResetPassword={handleConfirmResetPassword}
        />

        <AuthNavigation step={step} setStep={setStep} />
      </div>
    </div>
  );
}
