import { useEffect, useState } from 'react';
import { getStaffDirectory } from '../../api/staff';
import type { DirectoryDoctor } from '../../types';
import { extractErrorMessage } from '../../api/client';

export function StaffDirectoryPage() {
  const [items, setItems] = useState<DirectoryDoctor[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStaffDirectory()
      .then(setItems)
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  return (
    <div>
      <h1>Doctor Directory</h1>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Specialty</th>
            <th>Department</th>
            <th>Consultation Hours</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => (
            <tr key={d.doctor_id}>
              <td>{d.full_name}</td>
              <td>{d.specialty}</td>
              <td>{d.department_name}</td>
              <td>{d.consultation_hours}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && !error && <p className="muted">No doctors found.</p>}
    </div>
  );
}
