export const AUTH_STEPS = {
  SIGNUP: 'signup',
  SIGNIN: 'signin',
  VERIFY: 'verify',
  FORGOT_PASSWORD: 'forgot-password',
  RESET_PASSWORD: 'reset-password',
};

export const MESSAGE_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
};

export const STEP_TITLES = {
  [AUTH_STEPS.SIGNUP]: 'Create Account',
  [AUTH_STEPS.SIGNIN]: 'Welcome Back',
  [AUTH_STEPS.VERIFY]: 'Verify Email',
  [AUTH_STEPS.FORGOT_PASSWORD]: 'Reset Password',
  [AUTH_STEPS.RESET_PASSWORD]: 'Enter New Password',
};