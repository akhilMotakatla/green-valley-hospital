import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Calendar, Clock } from 'lucide-react';
import { getBlogArticle } from '../../api/public';
import type { BlogArticleDetail } from '../../types';
import { extractErrorMessage } from '../../api/client';
import { formatDate } from '../../utils/format';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';
import { BackToTopButton } from '../../components/BackToTopButton';

function ArticleHeader({ article }: { article: BlogArticleDetail }) {
  const [imgErr, setImgErr] = useState(false);

  return (
    <div style={{ position: 'relative', maxHeight: 400, overflow: 'hidden', marginBottom: '2rem' }}>
      {!imgErr && article.cover_image_path ? (
        <img
          src={article.cover_image_path}
          alt=""
          onError={() => setImgErr(true)}
          style={{
            width: '100%',
            height: 400,
            objectFit: 'cover',
            display: 'block',
          }}
        />
      ) : (
        <div
          style={{
            width: '100%',
            height: 300,
            background: 'linear-gradient(135deg, var(--color-primary-dark), var(--color-primary))',
          }}
        />
      )}
      {/* Dark overlay at bottom + title */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'linear-gradient(to top, rgba(0,0,0,0.75), transparent)',
          padding: '3rem 2rem 1.5rem',
        }}
      >
        <h1
          style={{
            color: '#fff',
            fontSize: '2rem',
            margin: 0,
            textShadow: '0 1px 3px rgba(0,0,0,0.3)',
          }}
        >
          {article.title}
        </h1>
      </div>
    </div>
  );
}

export function BlogArticlePage() {
  const { slug } = useParams();
  const [article, setArticle] = useState<BlogArticleDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    getBlogArticle(slug)
      .then((a) => { setArticle(a); setLoading(false); })
      .catch((e) => { setError(extractErrorMessage(e)); setLoading(false); });
  };

  useEffect(() => { load(); }, [slug]); // eslint-disable-line react-hooks/exhaustive-deps

  const readTime = article
    ? Math.ceil(article.body.split(/\s+/).length / 200)
    : 0;

  if (loading) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <SkeletonBlock lines={10} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '2rem 1.5rem' }}>
        <PageError message={error} onRetry={load} />
      </div>
    );
  }

  if (!article) return null;

  return (
    <div>
      {/* Back link */}
      <div className="container" style={{ padding: '1.5rem 1.5rem 0' }}>
        <Link
          to="/blog"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-primary)', fontWeight: 500 }}
        >
          <ArrowLeft size={18} /> Back to Blog
        </Link>
      </div>

      {/* Article header with cover image */}
      <ArticleHeader article={article} />

      <div className="container" style={{ padding: '0 1.5rem 4rem' }}>
        {/* Meta row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1.25rem',
            flexWrap: 'wrap',
            marginBottom: '2rem',
            fontSize: '0.875rem',
            color: 'var(--color-text-muted)',
            borderBottom: '1px solid var(--color-border)',
            paddingBottom: '1rem',
          }}
        >
          <span style={{ fontWeight: 600 }}>{article.author_name}</span>
          {article.published_at && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Calendar size={14} /> {formatDate(article.published_at)}
            </span>
          )}
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Clock size={14} /> {readTime} min read
          </span>
        </div>

        {/* Article body */}
        <div
          style={{
            maxWidth: 720,
            margin: '0 auto',
            fontSize: '1.0625rem',
            lineHeight: 1.75,
            color: 'var(--color-text)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {article.body}
        </div>
      </div>

      <BackToTopButton />
    </div>
  );
}
