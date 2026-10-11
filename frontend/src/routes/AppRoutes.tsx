import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { FullPageLoader } from '../components/ui/FullPageLoader'
import { AuthenticatedLayout } from '../layouts/AuthenticatedLayout'
import AdminLoginPage from '../pages/auth/AdminLoginPage'
import LoginPage from '../pages/auth/LoginPage'
import RegisterPage from '../pages/auth/RegisterPage'
import NotFoundPage from '../pages/errors/NotFoundPage'
import HomePage from '../pages/HomePage'
import type { Role } from '../types/auth'
import { GuestRoute } from './GuestRoute'
import { ProtectedRoute } from './ProtectedRoute'
import { RoleGuard } from './RoleGuard'

// Authenticated pages are lazy-loaded so each role only downloads what it uses.
const StudentDashboard = lazy(() => import('../pages/student/StudentDashboard'))
const ProblemsPage = lazy(() => import('../pages/student/ProblemsPage'))
const ProblemDetailPage = lazy(() => import('../pages/student/ProblemDetailPage'))
const CodingWorkspacePage = lazy(() => import('../pages/student/CodingWorkspacePage'))
const SubmissionsPage = lazy(() => import('../pages/student/SubmissionsPage'))
const SubmissionDetailPage = lazy(() => import('../pages/student/SubmissionDetailPage'))
const LearningPage = lazy(() => import('../pages/student/LearningPage'))
const TopicDetailPage = lazy(() => import('../pages/student/TopicDetailPage'))
const StaffDashboard = lazy(() => import('../pages/staff/StaffDashboard'))
const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard'))
const AdminUsers = lazy(() => import('../pages/admin/AdminUsers'))
const AdminSystem = lazy(() => import('../pages/admin/AdminSystem'))
const AdminProblems = lazy(() => import('../pages/admin/AdminProblems'))
const ProblemEditorPage = lazy(() => import('../pages/admin/ProblemEditorPage'))
const ProblemTestCasesPage = lazy(() => import('../pages/admin/ProblemTestCasesPage'))
const ProfilePage = lazy(() => import('../pages/shared/ProfilePage'))
const SettingsPage = lazy(() => import('../pages/shared/SettingsPage'))
const FeaturePage = lazy(() => import('../pages/shared/FeaturePage'))

const ALL_ROLES: Role[] = ['STUDENT', 'STAFF', 'ADMIN']

export function AppRoutes() {
  return (
    <Suspense fallback={<FullPageLoader message="Loading..." />}>
      <Routes>
        {/* Public */}
        <Route path="/" element={<HomePage />} />

        {/* Logged-out only; logged-in users are redirected to their dashboard */}
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
        </Route>

        {/* Authenticated: one shared layout, role-guarded sections */}
        <Route element={<ProtectedRoute allowedRoles={ALL_ROLES} />}>
          {/* Coding workspace: full-screen, outside the app shell, students only */}
          <Route element={<RoleGuard roles={['STUDENT']} fullPage />}>
            <Route path="/student/problems/:slug/solve" element={<CodingWorkspacePage />} />
          </Route>

          <Route element={<AuthenticatedLayout />}>
            <Route element={<RoleGuard roles={['STUDENT']} />}>
              <Route path="/student" element={<Navigate to="/student/dashboard" replace />} />
              <Route path="/student/dashboard" element={<StudentDashboard />} />
              <Route path="/student/problems" element={<ProblemsPage />} />
              <Route path="/student/problems/:slug" element={<ProblemDetailPage />} />
              <Route path="/student/submissions" element={<SubmissionsPage />} />
              <Route path="/student/submissions/:id" element={<SubmissionDetailPage />} />
              <Route path="/student/learning" element={<LearningPage />} />
              <Route path="/student/learning/:slug" element={<TopicDetailPage />} />
              <Route path="/student/contests" element={<FeaturePage feature="student-contests" />} />
              <Route path="/student/assignments" element={<FeaturePage feature="student-assignments" />} />
              <Route path="/student/leaderboard" element={<FeaturePage feature="student-leaderboard" />} />
              <Route path="/student/ai-tutor" element={<FeaturePage feature="student-ai-tutor" />} />
              <Route path="/student/profile" element={<ProfilePage />} />
            </Route>

            <Route element={<RoleGuard roles={['STAFF']} />}>
              <Route path="/staff" element={<Navigate to="/staff/dashboard" replace />} />
              <Route path="/staff/dashboard" element={<StaffDashboard />} />
              <Route path="/staff/classrooms" element={<FeaturePage feature="staff-classrooms" />} />
              <Route path="/staff/problems" element={<ProblemsPage key="staff" audience="staff" />} />
              <Route path="/staff/problems/:slug" element={<ProblemDetailPage audience="staff" />} />
              <Route path="/staff/assignments" element={<FeaturePage feature="staff-assignments" />} />
              <Route path="/staff/contests" element={<FeaturePage feature="staff-contests" />} />
              <Route path="/staff/students" element={<FeaturePage feature="staff-students" />} />
              <Route path="/staff/analytics" element={<FeaturePage feature="staff-analytics" />} />
              <Route path="/staff/profile" element={<ProfilePage />} />
            </Route>

            <Route element={<RoleGuard roles={['ADMIN']} />}>
              <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/students" element={<AdminUsers key="students" lockedRole="STUDENT" />} />
              <Route path="/admin/staff" element={<AdminUsers key="staff" lockedRole="STAFF" />} />
              <Route path="/admin/problems" element={<AdminProblems />} />
              <Route path="/admin/problems/new" element={<ProblemEditorPage key="new" />} />
              <Route path="/admin/problems/:id/edit" element={<ProblemEditorPage />} />
              <Route path="/admin/problems/:id/test-cases" element={<ProblemTestCasesPage />} />
              <Route path="/admin/system" element={<AdminSystem />} />
              <Route path="/admin/profile" element={<ProfilePage />} />
            </Route>

            {/* Global (any signed-in role) */}
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
