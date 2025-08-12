export const AuthInput = ({ 
  type = 'text', 
  placeholder, 
  value, 
  onChange, 
  className = 'auth-input' 
}) => {
  return (
    <div className="auth-input-group">
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={className}
      />
    </div>
  );
};