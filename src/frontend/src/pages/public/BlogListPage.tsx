import { useEffect, useRef, useState, type RefObject } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Calendar, ArrowRight } from 'lucide-react';
import { getBlogList } from '../../api/public';
import type { BlogListItem } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDate } from '../../utils/format';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { useScrollReveal } from '../../hooks/useScrollReveal';

function BlogCoverImage({ src, alt }: { src: string | null; alt: string }) {
  const [imgErr, setImgErr] = useState(false);

  if (!imgErr && src) {
    return (
      <img
        src={src}
        alt={alt}
        onError={() => setImgErr(true)}
        style={{
          width: '100%',
          height: 180,
          objectFit: 'cover',
          borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
          display: 'block',
        }}
      />
    );
  }

  return (
    <div
      style={{
        width: '100%',
        height: 180,
        borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
        background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
      }}
    >
      <BookOpen size={40} />
    </div>
  );
}

function AuthorAvatar({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
  return (
    <div
      style={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: 'var(--color-primary-light)',
        color: 'var(--color-primary-dark)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '0.65rem',
        fontWeight: 700,
        flexShrink: 0,
      }}
    >
      {initials}
    </div>
  );
}

export function BlogListPage() {
  const [items, setItems] = useState<BlogListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [heroBgErr, setHeroBgErr] = useState(false);
  const blogRef = useRef<HTMLDivElement>(null);
  useScrollReveal(blogRef as RefObject<HTMLElement | null>, !loading);

  const load = () => {
    setLoading(true);
    setError(null);
    getBlogList()
      .then((r) => { setItems(r.items); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      {/* Page hero */}
      <div className="page-hero" style={{ height: 'clamp(320px, 42vh, 460px)' }}>
        {!heroBgErr ? (
          <img src="/images/blog-hero.jpg" alt="" className="hero-bg" onError={() => setHeroBgErr(true)} />
        ) : (
          <div style={{ position: 'absolute', inset: 0, background: 'var(--color-primary-dark)' }} />
        )}
        <div className="hero-overlay" style={{ background: 'rgba(9,107,93,0.75)' }} />
        <div className="hero-content">
          <h1>Health Blog &amp; Articles</h1>
          <p>Expert health tips, news and insights from our medical team</p>
        </div>
      </div>

      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        {loading ? (
          <SkeletonBlock lines={6} />
        ) : error ? (
          <PageError message={error} onRetry={load} />
        ) : items.length === 0 ? (
          <div className="empty-state">
            <BookOpen size={80} color="var(--color-text-light)" />
            <h3>No articles published yet</h3>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              Check back soon for health tips and news.
            </p>
          </div>
        ) : (
          <div ref={blogRef} className="grid-3-up stagger-children">
            {items.map((a) => (
              <Link key={a.article_id} to={`/blog/${a.slug}`} className="reveal" style={{ textDecoration: 'none' }}>
                <div
                  className="card"
                  style={{
                    padding: 0,
                    overflow: 'hidden',
                    transition: 'transform 200ms ease, box-shadow 200ms ease',
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)';
                    (e.currentTarget as HTMLElement).style.boxShadow = 'var(--shadow-md)';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.transform = '';
                    (e.currentTarget as HTMLElement).style.boxShadow = '';
                  }}
                >
                  <BlogCoverImage src={a.cover_image_path} alt={a.title} />
                  <div style={{ padding: '1.25rem' }}>
                    <h3 className="line-clamp-2" style={{ marginBottom: '0.5rem' }}>{a.title}</h3>
                    <p
                      className="line-clamp-3"
                      style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', margin: '0 0 0.875rem' }}
                    >
                      {a.summary}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                      <AuthorAvatar name={a.author_name} />
                      <span>{a.author_name}</span>
                      {a.published_at && (
                        <>
                          <Calendar size={13} />
                          <span>{formatDate(a.published_at)}</span>
                        </>
                      )}
                    </div>
                    <div
                      style={{
                        marginTop: '0.75rem',
                        color: 'var(--color-primary)',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                      }}
                    >
                      Read More <ArrowRight size={14} />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
