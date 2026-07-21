import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { createDepartment, listDepartments, setDepartmentStatus, updateDepartment } from '../../api/admin';
import { adminListTags, adminAddTag, adminDeleteTag } from '../../api/search';
import type { SymptomTag } from '../../api/search';
import type { Department } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { Tag, Plus, X as XIcon, ChevronDown, ChevronUp } from 'lucide-react';

export function AdminDepartmentsPage() {
  const [items, setItems] = useState<Department[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [createMsg, setCreateMsg] = useState<string | null>(null);
  const [editing, setEditing] = useState<Record<number, { name: string; description: string }>>({});

  // Tags state per department
  const [expandedTags, setExpandedTags] = useState<number | null>(null);
  const [tags, setTags] = useState<Record<number, SymptomTag[]>>({});
  const [tagsLoading, setTagsLoading] = useState<number | null>(null);
  const [newTag, setNewTag] = useState<Record<number, string>>({});
  const [tagsError, setTagsError] = useState<Record<number, string>>({});

  const load = useCallback(() => {
    listDepartments()
      .then(setItems)
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function loadTags(deptId: number) {
    setTagsLoading(deptId);
    try {
      const data = await adminListTags(deptId);
      setTags((prev) => ({ ...prev, [deptId]: data }));
    } catch (err) {
      setTagsError((prev) => ({ ...prev, [deptId]: extractErrorMessage(err) }));
    } finally {
      setTagsLoading(null);
    }
  }

  function toggleTags(deptId: number) {
    if (expandedTags === deptId) {
      setExpandedTags(null);
    } else {
      setExpandedTags(deptId);
      if (!tags[deptId]) {
        loadTags(deptId);
      }
    }
  }

  async function handleAddTag(e: FormEvent, deptId: number) {
    e.preventDefault();
    const value = (newTag[deptId] ?? '').trim();
    if (!value) return;
    setTagsError((prev) => ({ ...prev, [deptId]: '' }));
    try {
      await adminAddTag(deptId, value);
      setNewTag((prev) => ({ ...prev, [deptId]: '' }));
      loadTags(deptId);
    } catch (err) {
      setTagsError((prev) => ({ ...prev, [deptId]: extractErrorMessage(err) }));
    }
  }

  async function handleDeleteTag(deptId: number, tagId: number) {
    try {
      await adminDeleteTag(deptId, tagId);
      loadTags(deptId);
    } catch (err) {
      setTagsError((prev) => ({ ...prev, [deptId]: extractErrorMessage(err) }));
    }
  }

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
            <th>Tags</th>
          </tr>
        </thead>
        <tbody>
          {items.map((d) => {
            const draft = editing[d.department_id];
            const isTagsOpen = expandedTags === d.department_id;
            const deptTags = tags[d.department_id] ?? [];
            return (
              <>
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
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => toggleTags(d.department_id)}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                      aria-expanded={isTagsOpen}
                    >
                      <Tag size={14} />
                      {isTagsOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </td>
                </tr>
                {isTagsOpen && (
                  <tr key={`tags-${d.department_id}`}>
                    <td colSpan={5} style={{ padding: '1rem 1.5rem', background: 'rgba(255,255,255,0.04)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                        <Tag size={16} />
                        <strong>Symptom Tags for {d.name}</strong>
                        <span className="muted" style={{ fontSize: '0.8rem' }}>({deptTags.length}/50)</span>
                      </div>
                      {tagsLoading === d.department_id ? (
                        <p className="muted">Loading tags...</p>
                      ) : (
                        <>
                          {tagsError[d.department_id] && (
                            <p style={{ color: 'var(--color-danger)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                              {tagsError[d.department_id]}
                            </p>
                          )}
                          {/* Tag chips */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
                            {deptTags.length === 0 && (
                              <span className="muted" style={{ fontSize: '0.85rem' }}>No tags yet.</span>
                            )}
                            {deptTags.map((t) => (
                              <span
                                key={t.tag_id}
                                style={{
                                  display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                                  background: 'var(--color-primary)', color: '#fff',
                                  padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem',
                                }}
                              >
                                {t.tag_text}
                                <button
                                  onClick={() => handleDeleteTag(d.department_id, t.tag_id)}
                                  style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center',
                                    padding: 0, lineHeight: 1,
                                  }}
                                  aria-label={`Remove tag ${t.tag_text}`}
                                >
                                  <XIcon size={12} />
                                </button>
                              </span>
                            ))}
                          </div>
                          {/* Add tag form */}
                          {deptTags.length < 50 && (
                            <form
                              onSubmit={(e) => handleAddTag(e, d.department_id)}
                              style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                            >
                              <input
                                type="text"
                                className="form-control"
                                style={{ maxWidth: 200, padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}
                                placeholder="Add tag..."
                                value={newTag[d.department_id] ?? ''}
                                onChange={(e) =>
                                  setNewTag((prev) => ({ ...prev, [d.department_id]: e.target.value }))
                                }
                                maxLength={80}
                              />
                              <button type="submit" className="btn btn-primary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <Plus size={14} /> Add
                              </button>
                            </form>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
      {items.length === 0 && !error && <p className="muted">No departments yet.</p>}
    </div>
  );
}
