export const AuthButton = ({ onClick, children, className = 'auth-button' }) => {
    return (
      <button onClick={onClick} className={className}>
        {children}
      </button>
    );
  };