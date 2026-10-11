import {
  ArrowDownUp,
  Binary,
  BookOpen,
  Brackets,
  Coins,
  GitBranch,
  Grid3x3,
  Hash,
  Layers,
  Link,
  ListOrdered,
  Repeat,
  Search,
  Share2,
  Terminal,
  Triangle,
  Type,
  Undo2,
  type LucideIcon,
} from 'lucide-react'

// Topics store a Lucide icon name in the database. Only known names render;
// anything else falls back to a book icon.
const ICONS: Record<string, LucideIcon> = {
  terminal: Terminal,
  brackets: Brackets,
  type: Type,
  search: Search,
  'arrow-down-up': ArrowDownUp,
  link: Link,
  layers: Layers,
  'list-ordered': ListOrdered,
  hash: Hash,
  repeat: Repeat,
  'git-branch': GitBranch,
  binary: Binary,
  triangle: Triangle,
  'share-2': Share2,
  coins: Coins,
  'undo-2': Undo2,
  'grid-3x3': Grid3x3,
}

export function TopicIcon({ name, className }: { name: string | null; className?: string }) {
  const Icon = (name && ICONS[name]) || BookOpen
  return <Icon className={className} aria-hidden />
}
