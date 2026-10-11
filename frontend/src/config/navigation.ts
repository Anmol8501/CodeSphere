import {
  BarChart3,
  Bot,
  BookOpen,
  ClipboardList,
  Code2,
  GraduationCap,
  History,
  LayoutDashboard,
  School,
  Server,
  Settings,
  Trophy,
  UserCog,
  UserRound,
  Users,
  type LucideIcon,
} from 'lucide-react'
import type { Role } from '../types/auth'

export interface NavItem {
  label: string
  icon: LucideIcon
  to: string
}

export interface NavSection {
  label: string
  items: NavItem[]
}

export const PORTAL_LABEL: Record<Role, string> = {
  STUDENT: 'Student Portal',
  STAFF: 'Staff Portal',
  ADMIN: 'Admin Console',
}

const SETTINGS: NavItem = { label: 'Settings', icon: Settings, to: '/settings' }

/**
 * Sidebar navigation per role. Hiding links is only a convenience: every API
 * endpoint enforces roles on the backend, and every route is role-guarded.
 */
export const NAV_SECTIONS: Record<Role, NavSection[]> = {
  STUDENT: [
    {
      label: 'Main',
      items: [
        { label: 'Dashboard', icon: LayoutDashboard, to: '/student/dashboard' },
        { label: 'Problems', icon: Code2, to: '/student/problems' },
        { label: 'Submissions', icon: History, to: '/student/submissions' },
        { label: 'Learning', icon: BookOpen, to: '/student/learning' },
        { label: 'Contests', icon: Trophy, to: '/student/contests' },
        { label: 'Assignments', icon: ClipboardList, to: '/student/assignments' },
        { label: 'Leaderboard', icon: BarChart3, to: '/student/leaderboard' },
        { label: 'AI Tutor', icon: Bot, to: '/student/ai-tutor' },
      ],
    },
    {
      label: 'System',
      items: [SETTINGS, { label: 'Profile', icon: UserRound, to: '/student/profile' }],
    },
  ],
  STAFF: [
    {
      label: 'Main',
      items: [
        { label: 'Dashboard', icon: LayoutDashboard, to: '/staff/dashboard' },
        { label: 'Classrooms', icon: School, to: '/staff/classrooms' },
        { label: 'Problems', icon: Code2, to: '/staff/problems' },
        { label: 'Assignments', icon: ClipboardList, to: '/staff/assignments' },
        { label: 'Contests', icon: Trophy, to: '/staff/contests' },
        { label: 'Students', icon: GraduationCap, to: '/staff/students' },
        { label: 'Analytics', icon: BarChart3, to: '/staff/analytics' },
      ],
    },
    {
      label: 'System',
      items: [SETTINGS, { label: 'Profile', icon: UserRound, to: '/staff/profile' }],
    },
  ],
  ADMIN: [
    {
      label: 'Main',
      items: [
        { label: 'Dashboard', icon: LayoutDashboard, to: '/admin/dashboard' },
        { label: 'Users', icon: Users, to: '/admin/users' },
        { label: 'Students', icon: GraduationCap, to: '/admin/students' },
        { label: 'Staff', icon: UserCog, to: '/admin/staff' },
        { label: 'Problems', icon: Code2, to: '/admin/problems' },
        { label: 'System', icon: Server, to: '/admin/system' },
      ],
    },
    { label: 'System', items: [SETTINGS] },
  ],
}

/** Pages reachable outside the sidebar that still need a title. */
const EXTRA_TITLES: Record<string, string> = {
  '/admin/profile': 'Profile',
}

export function isNavItemActive(item: NavItem, pathname: string): boolean {
  return pathname === item.to || pathname.startsWith(`${item.to}/`)
}

/** Title of the current page for the top navbar breadcrumb. */
export function getPageTitle(role: Role, pathname: string): string {
  for (const section of NAV_SECTIONS[role]) {
    const match = section.items.find((item) => isNavItemActive(item, pathname))
    if (match) return match.label
  }
  return EXTRA_TITLES[pathname] ?? 'CodeArena'
}
