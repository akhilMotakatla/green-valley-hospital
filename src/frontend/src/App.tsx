import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { RequireAuth } from './auth/RequireAuth';
import { PublicLayout } from './layouts/PublicLayout';
import { AppShell } from './layouts/AppShell';
import { SplashScreen } from './components/SplashScreen';

import { HomePage } from './pages/public/HomePage';
import { AboutPage } from './pages/public/AboutPage';
import { DepartmentsPage } from './pages/public/DepartmentsPage';
import { DepartmentDoctorsPage } from './pages/public/DepartmentDoctorsPage';
import { DoctorProfilePage as PublicDoctorProfilePage } from './pages/public/DoctorProfilePage';
import { ContactPage } from './pages/public/ContactPage';
import { BlogListPage } from './pages/public/BlogListPage';
import { BlogArticlePage } from './pages/public/BlogArticlePage';
import { LoginPage } from './pages/public/LoginPage';
import { SignupPage } from './pages/public/SignupPage';
import { UnauthorizedPage } from './pages/shared/UnauthorizedPage';
import { NotFoundPage } from './pages/shared/NotFoundPage';

import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminUsersPage } from './pages/admin/AdminUsersPage';
import { AdminDepartmentsPage } from './pages/admin/AdminDepartmentsPage';
import { AdminAppointmentsPage } from './pages/admin/AdminAppointmentsPage';
import { AdminInvoicesPage } from './pages/admin/AdminInvoicesPage';
import { AdminBlogPage } from './pages/admin/AdminBlogPage';
import { AdminContactMessagesPage } from './pages/admin/AdminContactMessagesPage';
import { AdminAuditLogPage } from './pages/admin/AdminAuditLogPage';

import { DoctorAppointmentsPage } from './pages/doctor/DoctorAppointmentsPage';
import { DoctorPatientRecordsPage } from './pages/doctor/DoctorPatientRecordsPage';
import { DoctorProfilePage } from './pages/doctor/DoctorProfilePage';

import { PatientAppointmentsPage } from './pages/patient/PatientAppointmentsPage';
import { BookAppointmentPage } from './pages/patient/BookAppointmentPage';
import { PatientRecordsPage } from './pages/patient/PatientRecordsPage';
import { PatientInvoicesPage } from './pages/patient/PatientInvoicesPage';
import { PatientProfilePage } from './pages/patient/PatientProfilePage';

import { StaffPatientsPage } from './pages/staff/StaffPatientsPage';
import { StaffPatientDetailPage } from './pages/staff/StaffPatientDetailPage';
import { RegisterPatientPage } from './pages/staff/RegisterPatientPage';
import { StaffAppointmentsPage } from './pages/staff/StaffAppointmentsPage';
import { StaffContactMessagesPage } from './pages/staff/StaffContactMessagesPage';
import { StaffDirectoryPage } from './pages/staff/StaffDirectoryPage';

import { LabOrdersPage } from './pages/lab/LabOrdersPage';

import { BillingDashboardPage } from './pages/billing/BillingDashboardPage';
import { BillingInvoicesPage } from './pages/billing/BillingInvoicesPage';
import { BillingPatientsPage } from './pages/billing/BillingPatientsPage';
import { BillingAppointmentsPage } from './pages/billing/BillingAppointmentsPage';
import { BillingNotificationsPage } from './pages/billing/BillingNotificationsPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SplashScreen />
        <Routes>
          {/* Public site */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/departments" element={<DepartmentsPage />} />
            <Route path="/departments/:id" element={<DepartmentDoctorsPage />} />
            <Route path="/doctors/:id" element={<PublicDoctorProfilePage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/blog" element={<BlogListPage />} />
            <Route path="/blog/:slug" element={<BlogArticlePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
          </Route>

          {/* Admin */}
          <Route
            element={
              <RequireAuth roles={['Admin']}>
                <AppShell roleLabel="Admin" />
              </RequireAuth>
            }
          >
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/departments" element={<AdminDepartmentsPage />} />
            <Route path="/admin/appointments" element={<AdminAppointmentsPage />} />
            <Route path="/admin/invoices" element={<AdminInvoicesPage />} />
            <Route path="/admin/blog" element={<AdminBlogPage />} />
            <Route path="/admin/contact-messages" element={<AdminContactMessagesPage />} />
            <Route path="/admin/audit-log" element={<AdminAuditLogPage />} />
          </Route>

          {/* Doctor */}
          <Route
            element={
              <RequireAuth roles={['Doctor']}>
                <AppShell roleLabel="Doctor" />
              </RequireAuth>
            }
          >
            <Route path="/doctor" element={<DoctorAppointmentsPage />} />
            <Route path="/doctor/patients/:patientId" element={<DoctorPatientRecordsPage />} />
            <Route path="/doctor/profile" element={<DoctorProfilePage />} />
          </Route>

          {/* Patient */}
          <Route
            element={
              <RequireAuth roles={['Patient']}>
                <AppShell roleLabel="Patient" />
              </RequireAuth>
            }
          >
            <Route path="/patient" element={<PatientAppointmentsPage />} />
            <Route path="/patient/book" element={<BookAppointmentPage />} />
            <Route path="/patient/records" element={<PatientRecordsPage />} />
            <Route path="/patient/invoices" element={<PatientInvoicesPage />} />
            <Route path="/patient/profile" element={<PatientProfilePage />} />
          </Route>

          {/* Staff */}
          <Route
            element={
              <RequireAuth roles={['Staff']}>
                <AppShell roleLabel="Staff" />
              </RequireAuth>
            }
          >
            <Route path="/staff" element={<StaffPatientsPage />} />
            <Route path="/staff/patients/:patientId" element={<StaffPatientDetailPage />} />
            <Route path="/staff/register" element={<RegisterPatientPage />} />
            <Route path="/staff/appointments" element={<StaffAppointmentsPage />} />
            <Route path="/staff/contact-messages" element={<StaffContactMessagesPage />} />
            <Route path="/staff/directory" element={<StaffDirectoryPage />} />
          </Route>

          {/* Lab */}
          <Route
            element={
              <RequireAuth roles={['Lab']}>
                <AppShell roleLabel="Lab" />
              </RequireAuth>
            }
          >
            <Route path="/lab" element={<LabOrdersPage />} />
          </Route>

          {/* Billing Specialist */}
          <Route
            element={
              <RequireAuth roles={['BillingSpecialist']}>
                <AppShell roleLabel="BillingSpecialist" />
              </RequireAuth>
            }
          >
            <Route path="/billing" element={<Navigate to="/billing/dashboard" replace />} />
            <Route path="/billing/dashboard" element={<BillingDashboardPage />} />
            <Route path="/billing/invoices" element={<BillingInvoicesPage />} />
            <Route path="/billing/patients" element={<BillingPatientsPage />} />
            <Route path="/billing/appointments" element={<BillingAppointmentsPage />} />
            <Route path="/billing/notifications" element={<BillingNotificationsPage />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
