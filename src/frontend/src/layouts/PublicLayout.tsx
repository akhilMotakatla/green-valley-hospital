import { useEffect, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { NavLink, Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  PhoneCall,
  Home,
  Info,
  Building2,
  BookOpen,
  Phone,
  Menu,
  X as XIcon,
  MapPin,
  Mail,
  Globe,
  Share2,
  Users,
  Send,
  CheckCircle,
  Search,
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Logo } from '../components/Logo';

const roleHome: Record<string, string> = {
  Admin: '/admin',
  Doctor: '/doctor',
  Patient: '/patient',
  Staff: '/staff',
  Lab: '/lab',
  BillingSpecialist: '/billing/dashboard',
};

const FOOTER_DEPARTMENTS = [
  { name: 'Cardiology',   id: 1 },
  { name: 'Pediatrics',   id: 2 },
  { name: 'Orthopedics',  id: 3 },
  { name: 'Neurology',    id: 4 },
  { name: 'Oncology',     id: 5 },
  { name: 'Radiology',    id: 6 },
];

export function PublicLayout() {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isHomePage = location.pathname === '/';
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const headerRef = useRef<HTMLElement>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (searchQuery.trim().length < 2) return;
    navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    setSearchQuery('');
  }

  function handleSearchKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      handleSearch(e as unknown as FormEvent);
    }
  }

  // Newsletter form state
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [newsletterSuccess, setNewsletterSuccess] = useState(false);

  // Scroll shadow on nav
  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 20);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close hamburger on outside click
  useEffect(() => {
    if (!menuOpen) return;
    function onMouseDown(e: MouseEvent) {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, [menuOpen]);

  function handleNewsletter(e: FormEvent) {
    e.preventDefault();
    if (!newsletterEmail.trim()) return;
    setNewsletterSuccess(true);
    setNewsletterEmail('');
    setTimeout(() => setNewsletterSuccess(false), 5000);
  }

  const navLinks = [
    { to: '/', label: 'Home', icon: <Home size={16} />, end: true },
    { to: '/about', label: 'About', icon: <Info size={16} /> },
    { to: '/departments', label: 'Departments', icon: <Building2 size={16} /> },
    { to: '/blog', label: 'Blog', icon: <BookOpen size={16} /> },
    { to: '/contact', label: 'Contact', icon: <Phone size={16} /> },
    { to: '/corporate', label: 'For Organizations', icon: <Building2 size={16} /> },
  ];

  return (
    <div className="site public-page">
      {/* ---- Emergency strip ---- */}
      <div className="emergency-strip" style={{ background: 'var(--color-primary-deeper)', justifyContent: 'center', gap: '0.5rem' }}>
        <span className="pulse-phone"><PhoneCall size={14} /></span>
        Emergency:&nbsp;<span className="emergency-number" style={{ color: 'var(--color-accent)', fontWeight: 600 }}>+1 (555) 000-9999</span>
        <span className="emergency-secondary" style={{ color: 'rgba(255,255,255,0.85)' }}>&nbsp;|&nbsp;Open 24 hours, 7 days a week</span>
      </div>

      {/* ---- Navbar ---- */}
      <header
        className={`public-nav${scrolled ? ' scrolled' : ''}${isHomePage && !scrolled ? ' homepage-transparent' : ''}`}
        ref={headerRef}
        style={isHomePage && !scrolled ? { background: 'transparent', borderBottomColor: 'transparent' } : undefined}
      >
        <Link to="/" style={{ textDecoration: 'none', flexShrink: 0 }}>
          <Logo variant="default" size={38} />
        </Link>

        {/* Desktop nav */}
        <nav aria-label="Main navigation">
          {navLinks.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.icon} {l.label}
            </NavLink>
          ))}
        </nav>

        {/* Desktop search bar (>= 768px) */}
        <form
          onSubmit={handleSearch}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '20px',
            padding: '0.25rem 0.5rem 0.25rem 0.75rem',
          }}
          role="search"
          aria-label="Search symptoms, conditions, doctors"
        >
          <Search size={14} style={{ opacity: 0.7, flexShrink: 0 }} />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search symptoms, doctors..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'inherit',
              width: 160,
              fontSize: '0.8rem',
            }}
            aria-label="Search query"
          />
        </form>

        <div className="nav-auth">
          {isAuthenticated && user ? (
            <>
              <Link to={roleHome[user.role] ?? '/'} className="btn btn-ghost btn-sm">
                My Dashboard
              </Link>
              <button className="btn btn-outline btn-sm" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost btn-sm">
                Login
              </Link>
              <Link to="/signup" className="btn btn-sm btn-book-appointment">
                Book Appointment
              </Link>
            </>
          )}
        </div>

        {/* Hamburger */}
        <button
          className="hamburger"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
        >
          {menuOpen ? <XIcon size={22} /> : <Menu size={22} />}
        </button>

        {/* Mobile dropdown */}
        <div className={`mobile-menu${menuOpen ? ' open' : ''}`}>
          {/* Mobile search */}
          <form
            onSubmit={handleSearch}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              padding: '0.5rem 0.75rem',
              marginBottom: '0.5rem',
            }}
            role="search"
          >
            <Search size={16} style={{ opacity: 0.7, flexShrink: 0 }} />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Search symptoms, doctors..."
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'inherit',
                flex: 1,
                fontSize: '0.9rem',
              }}
            />
            <button type="submit" className="btn btn-ghost btn-sm" style={{ padding: '0.25rem 0.5rem' }}>Go</button>
          </form>
          {navLinks.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              onClick={() => setMenuOpen(false)}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.25rem' }}
            >
              {l.icon} {l.label}
            </NavLink>
          ))}
          <hr style={{ border: 'none', borderTop: '1px solid var(--color-border)', margin: '0.5rem 0' }} />
          {isAuthenticated && user ? (
            <>
              <Link to={roleHome[user.role] ?? '/'} className="btn btn-ghost" onClick={() => setMenuOpen(false)}>
                My Dashboard
              </Link>
              <button className="btn btn-outline" onClick={() => { setMenuOpen(false); logout(); }}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline" onClick={() => setMenuOpen(false)}>
                Login
              </Link>
              <Link to="/signup" className="btn btn-gradient btn-pill" onClick={() => setMenuOpen(false)}>
                Book Appointment
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Page content */}
      <main className="page-root" id="main-content">
        <Outlet />
      </main>

      {/* ---- 4-column footer ---- */}
      <footer className="public-footer">
        <div className="footer-grid">
          {/* Column 1 — Brand + newsletter */}
          <div className="footer-col">
            <Logo variant="white" size={34} />
            <p style={{ marginTop: '0.875rem' }}>
              Compassionate, modern healthcare for you and your family — every day.
            </p>
            <div className="footer-social">
              <a href="#" aria-label="Website"><Globe size={16} /></a>
              <a href="#" aria-label="Social"><Share2 size={16} /></a>
              <a href="#" aria-label="Community"><Users size={16} /></a>
            </div>
            <div className="footer-newsletter">
              <p style={{ fontWeight: 600, color: 'rgba(255,255,255,0.9)', fontSize: '0.8rem', marginBottom: '0.25rem', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                Health Newsletter
              </p>
              {newsletterSuccess ? (
                <div className="footer-newsletter-success">
                  <CheckCircle size={16} />
                  Thank you for subscribing!
                </div>
              ) : (
                <form onSubmit={handleNewsletter} className="footer-newsletter form">
                  <input
                    type="email"
                    value={newsletterEmail}
                    onChange={(e) => setNewsletterEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                  />
                  <button type="submit">
                    <Send size={14} />
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Column 2 — Quick Links */}
          <div className="footer-col">
            <h4>Quick Links</h4>
            <Link to="/about">About Us</Link>
            <Link to="/departments">Departments</Link>
            <Link to="/blog">Health Blog</Link>
            <Link to="/contact">Contact</Link>
            <Link to="/signup">Book Appointment</Link>
            <Link to="/login">Patient Login</Link>
          </div>

          {/* Column 3 — Services */}
          <div className="footer-col">
            <h4>Our Services</h4>
            {FOOTER_DEPARTMENTS.map((d) => (
              <Link key={d.id} to={`/departments/${d.id}`}>{d.name}</Link>
            ))}
          </div>

          {/* Column 4 — Contact Info */}
          <div className="footer-col">
            <h4>Contact Us</h4>
            <div className="footer-contact-row">
              <div className="icon-circle"><MapPin size={14} /></div>
              <span>123 Green Valley Drive, Medical District, City, State 00000</span>
            </div>
            <div className="footer-contact-row">
              <div className="icon-circle"><Phone size={14} /></div>
              <span>+1 (555) 000-1234</span>
            </div>
            <div className="footer-contact-row">
              <div className="icon-circle"><PhoneCall size={14} /></div>
              <span className="emergency-number">+1 (555) 000-9999</span>
            </div>
            <div className="footer-contact-row">
              <div className="icon-circle"><Mail size={14} /></div>
              <span>info@greenvalleyhospital.demo</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <span>&copy; {new Date().getFullYear()} Green Valley Hospital. All rights reserved.</span>
          <span>
            <a href="#">Privacy Policy</a>
            &nbsp;|&nbsp;
            <a href="#">Terms of Use</a>
            &nbsp;|&nbsp;
            <a href="#">Accessibility</a>
          </span>
        </div>
      </footer>
    </div>
  );
}
