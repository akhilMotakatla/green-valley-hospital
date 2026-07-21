import { NavLink, Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  CalendarCheck,
  Users,
  FileText,
  Receipt,
  UserCircle,
  FlaskConical,
  BookOpen,
  UserCog,
  MessageSquare,
  ClipboardList,
  Building2,
  LogOut,
  Bell,
  CalendarPlus,
  CalendarClock,
} from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Logo } from '../components/Logo';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const navByRole: Record<string, NavItem[]> = {
  Admin: [
    { to: '/admin',                   label: 'Dashboard',        icon: <LayoutDashboard size={16} /> },
    { to: '/admin/users',             label: 'Users',            icon: <UserCog size={16} /> },
    { to: '/admin/departments',       label: 'Departments',      icon: <Building2 size={16} /> },
    { to: '/admin/appointments',      label: 'Appointments',     icon: <CalendarCheck size={16} /> },
    { to: '/admin/invoices',          label: 'Billing',          icon: <Receipt size={16} /> },
    { to: '/admin/blog',              label: 'Blog',             icon: <BookOpen size={16} /> },
    { to: '/admin/contact-messages',  label: 'Contact Messages', icon: <MessageSquare size={16} /> },
    { to: '/admin/audit-log',         label: 'Audit Log',        icon: <ClipboardList size={16} /> },
  ],
  Doctor: [
    { to: '/doctor',              label: 'Appointments', icon: <CalendarCheck size={16} /> },
    { to: '/doctor/availability', label: 'Schedule',     icon: <CalendarClock size={16} /> },
    { to: '/doctor/profile',      label: 'My Profile',   icon: <UserCircle size={16} /> },
  ],
  Patient: [
    { to: '/patient',          label: 'My Appointments', icon: <CalendarCheck size={16} /> },
    { to: '/patient/book',     label: 'Book Appointment', icon: <CalendarPlus size={16} /> },
    { to: '/patient/records',  label: 'My Records',       icon: <FileText size={16} /> },
    { to: '/patient/invoices', label: 'My Billing',       icon: <Receipt size={16} /> },
    { to: '/patient/profile',  label: 'My Profile',       icon: <UserCircle size={16} /> },
  ],
  Staff: [
    { to: '/staff',                   label: 'Patients',         icon: <Users size={16} /> },
    { to: '/staff/register',          label: 'Register Patient', icon: <UserCircle size={16} /> },
    { to: '/staff/appointments',      label: 'Appointments',     icon: <CalendarCheck size={16} /> },
    { to: '/staff/contact-messages',  label: 'Contact Messages', icon: <MessageSquare size={16} /> },
    { to: '/staff/directory',         label: 'Doctor Directory', icon: <Users size={16} /> },
  ],
  Lab: [
    { to: '/lab', label: 'Order Queue', icon: <FlaskConical size={16} /> },
  ],
  BillingSpecialist: [
    { to: '/billing/dashboard',     label: 'Dashboard',    icon: <LayoutDashboard size={16} /> },
    { to: '/billing/invoices',      label: 'Invoices',     icon: <Receipt size={16} /> },
    { to: '/billing/patients',      label: 'Patients',     icon: <Users size={16} /> },
    { to: '/billing/appointments',  label: 'Appointments', icon: <CalendarCheck size={16} /> },
    { to: '/billing/notifications', label: 'Notifications', icon: <Bell size={16} /> },
  ],
};

function usePageTitle(role: string): string {
  const location = useLocation();
  const items = navByRole[role] ?? [];
  const sorted = [...items].sort((a, b) => b.to.length - a.to.length);
  const match = sorted.find(
    (item) => location.pathname === item.to || location.pathname.startsWith(item.to + '/'),
  );
  return match?.label ?? 'Dashboard';
}

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return fullName.slice(0, 2).toUpperCase() || '?';
}

export function AppShell({ roleLabel }: { roleLabel: string }) {
  const { user, logout } = useAuth();
  const items       = user ? navByRole[user.role] ?? [] : [];
  const pageTitle   = usePageTitle(user?.role ?? '');
  const displayName = user?.fullName || user?.email || '';
  const initials    = user ? getInitials(user.fullName || user.email) : '?';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Logo variant="white" size={32} />
          </Link>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === `/${roleLabel.toLowerCase()}` || item.to === '/billing/dashboard'}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User info block */}
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{displayName}</div>
            <div className="sidebar-user-role">{roleLabel}</div>
          </div>
          <button
            className="sidebar-logout-btn"
            onClick={logout}
            title="Log out"
            aria-label="Log out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <div className="app-content">
        {/* Topbar */}
        <header className="topbar">
          <span className="topbar-title">{pageTitle}</span>
          <div className="topbar-right">
            <span className="topbar-user-name">{displayName}</span>
            <span className="topbar-role-badge">{roleLabel}</span>
            <button className="topbar-icon-btn" aria-label="Notifications" title="Notifications">
              <Bell size={18} />
            </button>
            <button className="topbar-icon-btn" onClick={logout} aria-label="Logout" title="Logout">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
