export const AuthMessage = ({ message, messageType }) => {
  if (!message) return null;

  return (
    <div className={`auth-message ${messageType}`}>
      {message}
    </div>
  );
};
