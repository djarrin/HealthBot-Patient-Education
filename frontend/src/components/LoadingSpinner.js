export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      fontSize: '1.125rem',
      color: '#4a5568',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {message}
    </div>
  );
}
