import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { createDepartment, listDepartments, setDepartmentStatus, updateDepartment } from '../../api/admin';
import type { Department } from '../../types';
import { extractErrorMessage } from '../../api/client';

export function AdminDepartmentsPage() {
  const [items, setItems] = useState<Department[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [createMsg, setCreateMsg] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<number, { name: string; description: string }>>({});

  const load = useCallback(() => {
    listDepartments()
      .then(setItems)
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateMsg(null);
    try {
      await createDepartment(name, description);
      setCreateMsg('Department created.');
      setName('');
      setDescription('');
      load();
    } catch (err) {
      setCreateMsg(extractErrorMessage(err));
    }
  }

  async function toggleActive(d: Department) {
    try {
      await setDepartmentStatus(d.department_id, !d.is_active);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function saveEdit(d: Department) {
    const draft = editing[d.department_id];
    if (!draft) return;
    try {
      await updateDepartment(d.department_id, draft);
      setEditing((prev) => {
        const next = { ...prev };
        delete next[d.department_id];
        return next;
      });
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Departments</h1>
      <section className="section card">
        <h2>Add Department</h2>
        {createMsg && (
          <p className={createMsg.includes('created') ? 'success-text' : 'error-text'}>{createMsg}</p>
        )}
        <form className="form" onSubmit={handleCreate}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Description
            <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">
            Add Department
          </button>
        </form>
      </section>

      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => {
            const draft = editing[d.department_id];
            return (
              <tr key={d.department_id}>
                <td>
                  {draft ? (
                    <input
                      value={draft.name}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [d.department_id]: { ...draft, name: e.target.value },
                        }))
                      }
                    />
                  ) : (
                    d.name
                  )}
                </td>
                <td>
                  {draft ? (
                    <input
                      value={draft.description}
                      onChange={(e) =>
                        setEditing((prev) => ({
                          ...prev,
                          [d.department_id]: { ...draft, description: e.target.value },
                        }))
                      }
                    />
                  ) : (
                    d.description
                  )}
                </td>
                <td>{d.is_active ? 'Active' : 'Inactive'}</td>
                <td style={{ display: 'flex', gap: '0.4rem' }}>
                  {draft ? (
                    <button className="btn btn-primary" onClick={() => saveEdit(d)}>
                      Save
                    </button>
                  ) : (
                    <button
                      className="btn btn-outline"
                      onClick={() =>
                        setEditing((prev) => ({
                          ...prev,
                          [d.department_id]: { name: d.name, description: d.description ?? '' },
                        }))
                      }
                    >
                      Edit
                    </button>
                  )}
                  <button className="btn btn-outline" onClick={() => toggleActive(d)}>
                    {d.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {items.length === 0 && !error && <p className="muted">No departments yet.</p>}
    </div>
  );
}
