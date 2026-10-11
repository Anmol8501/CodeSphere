import {
  BarChart3,
  Bot,
  ClipboardList,
  GraduationCap,
  School,
  Trophy,
  type LucideIcon,
} from 'lucide-react'

/**
 * Pages for features that are planned but not built yet. Each one renders an
 * honest empty state plus the list of capabilities that are planned.
 */
export interface FeatureDefinition {
  eyebrow: string
  title: string
  description: string
  icon: LucideIcon
  emptyTitle: string
  emptyDescription: string
  planned: string[]
  action?: { label: string; to: string }
}

export const FEATURES = {
  'student-contests': {
    eyebrow: 'Compete',
    title: 'Contests',
    description: 'Timed coding contests with live rankings.',
    icon: Trophy,
    emptyTitle: 'No contests yet.',
    emptyDescription: 'Contests will appear here when your college or staff schedule them.',
    planned: ['Scheduled and live contests', 'Real-time scoreboard', 'Contest rating history'],
    action: { label: 'Explore Problems', to: '/student/problems' },
  },
  'student-assignments': {
    eyebrow: 'Classroom',
    title: 'Assignments',
    description: 'Coding assignments from your classroom staff.',
    icon: ClipboardList,
    emptyTitle: 'No assignments yet.',
    emptyDescription: 'Assignments from your staff will show up here with their deadlines.',
    planned: ['Classroom assignments with deadlines', 'Automatic evaluation', 'Feedback from staff'],
  },
  'student-leaderboard': {
    eyebrow: 'Rankings',
    title: 'Leaderboard',
    description: 'See how you rank against other students.',
    icon: BarChart3,
    emptyTitle: 'No rankings yet.',
    emptyDescription: 'Rankings are calculated from solved problems and contests, which are not live yet.',
    planned: ['College and classroom rankings', 'Weekly and all-time boards', 'Contest standings'],
  },
  'student-ai-tutor': {
    eyebrow: 'Assistant',
    title: 'AI Tutor',
    description: 'Hints, explanations and code review powered by AI.',
    icon: Bot,
    emptyTitle: 'AI Tutor is not available yet.',
    emptyDescription: 'The AI service is not connected. It will help with hints and explanations once enabled.',
    planned: ['Step-by-step hints without spoilers', 'Concept explanations', 'Code review on your submissions'],
  },
  'staff-classrooms': {
    eyebrow: 'Teaching',
    title: 'Classrooms',
    description: 'Create classrooms and invite students.',
    icon: School,
    emptyTitle: 'No classrooms created yet.',
    emptyDescription: 'Classroom management will let you group students and share work with them.',
    planned: ['Create classrooms and invite codes', 'Student rosters', 'Classroom announcements'],
  },
  'staff-assignments': {
    eyebrow: 'Teaching',
    title: 'Assignments',
    description: 'Publish assignments to your classrooms.',
    icon: ClipboardList,
    emptyTitle: 'No assignments created yet.',
    emptyDescription: 'Assignments need classrooms and problems, which arrive in later phases.',
    planned: ['Assignments with deadlines', 'Automatic grading', 'Late submission rules'],
  },
  'staff-contests': {
    eyebrow: 'Competition',
    title: 'Contests',
    description: 'Host timed contests for your students.',
    icon: Trophy,
    emptyTitle: 'No contests created yet.',
    emptyDescription: 'Contest hosting arrives after the judge engine is connected.',
    planned: ['Contest scheduling', 'Live scoreboard', 'Plagiarism checks'],
  },
  'staff-students': {
    eyebrow: 'Teaching',
    title: 'Students',
    description: 'Students enrolled in your classrooms.',
    icon: GraduationCap,
    emptyTitle: 'No students yet.',
    emptyDescription: 'Students will appear here once they join one of your classrooms.',
    planned: ['Roster per classroom', 'Individual progress views', 'Submission history'],
  },
  'staff-analytics': {
    eyebrow: 'Insights',
    title: 'Analytics',
    description: 'Performance insights across your classrooms.',
    icon: BarChart3,
    emptyTitle: 'No student performance data available yet.',
    emptyDescription: 'Analytics are built from submissions, which start once the judge engine is connected.',
    planned: ['Topic-wise class performance', 'At-risk student detection', 'Assignment completion trends'],
  },
} satisfies Record<string, FeatureDefinition>

export type FeatureKey = keyof typeof FEATURES
