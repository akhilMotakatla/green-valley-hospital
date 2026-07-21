import { Link } from 'react-router-dom';

export function UnauthorizedPage() {
  return (
    <div className="center-box">
      <h1>Not Authorized</h1>
      <p>You don't have permission to view this page.</p>
      <Link to="/" className="btn btn-primary">
        Go home
      </Link>
    </div>
  );
}
