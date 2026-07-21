import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarPlus, ShieldCheck, Star, ChevronDown } from 'lucide-react';

const HERO_IMAGE = '/images/hero-banner.jpg';

/**
 * Full-screen (100svh) cinematic homepage hero: one full-bleed photograph,
 * a dark cinematic gradient overlay for text legibility, an asymmetrical
 * editorial content block (left-aligned, not centered), a floating glass
 * accolade panel, and a subtle scroll-linked parallax on the background
 * image (disabled under `prefers-reduced-motion`).
 */
export function MosaicHero() {
  const [visible, setVisible] = useState(false);
  const [parallax, setParallax] = useState(0);
  const reduceMotionRef = useRef(false);

  useEffect(() => {
    reduceMotionRef.current = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const t = window.setTimeout(() => setVisible(true), 80);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    if (reduceMotionRef.current) return;
    let raf = 0;
    function onScroll() {
      raf = requestAnimationFrame(() => {
        setParallax(Math.min(window.scrollY * 0.28, 160));
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section className="cinematic-hero" aria-label="Green Valley Hospital hero">
      <div
        className="cinematic-hero-bg"
        style={{
          backgroundImage: `url(${HERO_IMAGE})`,
          transform: `translateY(${parallax}px) scale(1.08)`,
        }}
      />
      <div className="cinematic-hero-overlay" />

      <div className={`cinematic-hero-content${visible ? ' is-visible' : ''}`}>
        <div className="mosaic-hero-eyebrow">Trusted Healthcare Since 1998</div>
        <h1 className="hero-title">
          World-Class Healthcare,
          <br />
          Close to Home
        </h1>
        <p className="cinematic-hero-tagline">
          Compassionate doctors. Cutting-edge technology. Your health, our purpose.
        </p>
        <div className="mosaic-hero-ctas">
          <Link to="/signup" className="btn btn-pill mosaic-cta-primary">
            <CalendarPlus size={18} /> Book an Appointment
          </Link>
          <Link to="/departments" className="btn btn-pill glass-btn">
            Explore Departments
          </Link>
        </div>
      </div>

      <div className={`cinematic-hero-float-card glass-panel${visible ? ' is-visible' : ''}`}>
        <div className="mosaic-hero-float-row">
          <ShieldCheck size={18} color="var(--color-gold)" />
          <span>Regional Recognition</span>
        </div>
        <div className="mosaic-hero-float-rank">Ranked #1 in the Region</div>
        <div className="mosaic-hero-float-stars">
          {[1, 2, 3, 4, 5].map((s) => (
            <Star key={s} size={14} fill="var(--color-gold)" color="var(--color-gold)" />
          ))}
        </div>
      </div>

      <div className="cinematic-hero-scroll-cue" aria-hidden="true">
        <ChevronDown size={22} />
      </div>
    </section>
  );
}
