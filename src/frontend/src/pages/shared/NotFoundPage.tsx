import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="center-box">
      <h1>Page Not Found</h1>
      <Link to="/" className="btn btn-primary">
        Go home
      </Link>
    </div>
  );
}
