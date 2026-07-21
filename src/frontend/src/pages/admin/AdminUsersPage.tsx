import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { createUser, listUsers, setUserRole, setUserStatus } from '../../api/admin';
import type { Role, User } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { Pager } from '../../components/Pager';

type CreatableRole = 'Admin' | 'Doctor' | 'Staff' | 'Lab' | 'BillingSpecialist';

const roles: Role[] = ['Admin', 'Doctor', 'Patient', 'Staff', 'Lab', 'BillingSpecialist'];
const creatableRoles: CreatableRole[] = ['Doctor', 'Staff', 'Lab', 'Admin', 'BillingSpecialist'];

export function AdminUsersPage() {
  const [items, setItems] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [roleFilter, setRoleFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const pageSize = 15;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [role, setRole] = useState<CreatableRole>('Doctor');
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    listUsers({ role: (roleFilter as Role) || undefined, page, page_size: pageSize })
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, [roleFilter, page]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateMsg(null);
    try {
      await createUser({ email, password, role, full_name: fullName, phone });
      setCreateMsg('User created.');
      setEmail('');
      setPassword('');
      setFullName('');
      setPhone('');
      load();
    } catch (err) {
      setCreateMsg(extractErrorMessage(err));
    }
  }

  async function toggleActive(user: User) {
    try {
      await setUserStatus(user.id, !user.is_active);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function changeRole(user: User, newRole: Role) {
    try {
      await setUserRole(user.id, newRole);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Users</h1>

      <section className="section card">
        <h2>Create Staff / Doctor / Lab / Admin Account</h2>
        {createMsg && (
          <p className={createMsg.includes('created') ? 'success-text' : 'error-text'}>{createMsg}</p>
        )}
        <form className="form" onSubmit={handleCreate}>
          <label>
            Full name
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Temporary password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <label>
            Phone
            <input value={phone} onChange={(e) => setPhone(e.target.value)} required />
          </label>
          <label>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value as CreatableRole)}>
              {creatableRoles.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <button className="btn btn-primary" type="submit">
            Create User
          </button>
        </form>
      </section>

      <div className="toolbar">
        <label>
          Filter by role
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            {roles.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((u) => (
            <tr key={u.id}>
              <td>{u.full_name}</td>
              <td>{u.email}</td>
              <td>
                <select value={u.role} onChange={(e) => changeRole(u, e.target.value as Role)}>
                  {roles.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </td>
              <td>{u.is_active ? 'Active' : 'Inactive'}</td>
              <td>
                <button className="btn btn-outline" onClick={() => toggleActive(u)}>
                  {u.is_active ? 'Deactivate' : 'Reactivate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="muted">No users found.</p>}
      <Pager page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
    </div>
  );
}
