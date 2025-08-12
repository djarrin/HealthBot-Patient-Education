import { AUTH_STEPS } from './authConstants';

export const AuthNavigation = ({ step, setStep }) => {
  const renderSigninNavigation = () => (
    <>
      <button 
        onClick={() => setStep(AUTH_STEPS.SIGNUP)}
        className="auth-navigation-button"
      >
        Need an account? Sign up
      </button>
      <br />
      <button 
        onClick={() => setStep(AUTH_STEPS.FORGOT_PASSWORD)}
        className="auth-navigation-button"
      >
        Forgot your password?
      </button>
    </>
  );

  const renderSignupNavigation = () => (
    <button 
      onClick={() => setStep(AUTH_STEPS.SIGNIN)}
      className="auth-navigation-button"
    >
      Already have an account? Sign in
    </button>
  );

  const renderVerifyNavigation = () => (
    <button 
      onClick={() => setStep(AUTH_STEPS.SIGNIN)}
      className="auth-navigation-button"
    >
      Back to Sign In
    </button>
  );

  const renderForgotPasswordNavigation = () => (
    <button 
      onClick={() => setStep(AUTH_STEPS.SIGNIN)}
      className="auth-navigation-button"
    >
      Back to Sign In
    </button>
  );

  const renderResetPasswordNavigation = () => (
    <button 
      onClick={() => setStep(AUTH_STEPS.FORGOT_PASSWORD)}
      className="auth-navigation-button"
    >
      Back to Reset Password
    </button>
  );

  const getNavigationContent = () => {
    switch (step) {
      case AUTH_STEPS.SIGNIN:
        return renderSigninNavigation();
      case AUTH_STEPS.SIGNUP:
        return renderSignupNavigation();
      case AUTH_STEPS.VERIFY:
        return renderVerifyNavigation();
      case AUTH_STEPS.FORGOT_PASSWORD:
        return renderForgotPasswordNavigation();
      case AUTH_STEPS.RESET_PASSWORD:
        return renderResetPasswordNavigation();
      default:
        return null;
    }
  };

  return (
    <div className="auth-navigation">
      {getNavigationContent()}
    </div>
  );
};
