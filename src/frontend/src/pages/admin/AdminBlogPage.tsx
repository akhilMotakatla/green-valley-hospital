import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import {
  createBlogArticle,
  deleteBlogArticle,
  listAdminBlog,
  publishBlogArticle,
  unpublishBlogArticle,
} from '../../api/admin';
import { extractErrorMessage } from '../../api/client';

interface AdminBlogItem {
  article_id: number;
  title: string;
  slug: string;
  status: 'Draft' | 'Published';
  published_at: string | null;
}

export function AdminBlogPage() {
  const [items, setItems] = useState<AdminBlogItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [body, setBody] = useState('');
  const [coverImage, setCoverImage] = useState<File | null>(null);
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    listAdminBlog({ page: 1, page_size: 50 })
      .then((r) => setItems(r.items as unknown as AdminBlogItem[]))
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateMsg(null);
    try {
      await createBlogArticle({ title, summary, body, cover_image: coverImage ?? undefined });
      setCreateMsg('Article created as Draft.');
      setTitle('');
      setSummary('');
      setBody('');
      setCoverImage(null);
      load();
    } catch (err) {
      setCreateMsg(extractErrorMessage(err));
    }
  }

  async function handlePublishToggle(item: AdminBlogItem) {
    try {
      if (item.status === 'Published') {
        await unpublishBlogArticle(item.article_id);
      } else {
        await publishBlogArticle(item.article_id);
      }
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteBlogArticle(id);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <h1>Blog Administration</h1>

      <section className="section card">
        <h2>New Article</h2>
        {createMsg && (
          <p className={createMsg.includes('created') ? 'success-text' : 'error-text'}>{createMsg}</p>
        )}
        <form className="form" onSubmit={handleCreate}>
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            Summary
            <textarea rows={2} value={summary} onChange={(e) => setSummary(e.target.value)} required />
          </label>
          <label>
            Body
            <textarea rows={6} value={body} onChange={(e) => setBody(e.target.value)} required />
          </label>
          <label>
            Cover image (optional)
            <input type="file" accept="image/*" onChange={(e) => setCoverImage(e.target.files?.[0] ?? null)} />
          </label>
          <button className="btn btn-primary" type="submit">
            Save as Draft
          </button>
        </form>
      </section>

      {error && <p className="error-text">{error}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Status</th>
            <th>Published</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.article_id}>
              <td>{a.title}</td>
              <td>{a.status}</td>
              <td>{a.published_at ?? '—'}</td>
              <td style={{ display: 'flex', gap: '0.4rem' }}>
                <button className="btn btn-outline" onClick={() => handlePublishToggle(a)}>
                  {a.status === 'Published' ? 'Unpublish' : 'Publish'}
                </button>
                <button className="btn btn-danger" onClick={() => handleDelete(a.article_id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && !error && <p className="muted">No articles yet.</p>}
    </div>
  );
}
