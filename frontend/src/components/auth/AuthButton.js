export const AuthButton = ({ onClick, children, className = 'auth-button', type = 'button' }) => {
  return (
    <button type={type} onClick={onClick} className={className}>
      {children}
    </button>
  );
};