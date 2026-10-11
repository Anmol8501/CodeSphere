import { CircleDashed, Sparkles } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { SectionCard } from '../../components/ui/Card'
import { EmptyState } from '../../components/ui/EmptyState'
import { PageHeader } from '../../components/ui/PageHeader'
import { FEATURES, type FeatureKey } from '../../config/features'

/**
 * Page for a feature that is planned but not built yet: an honest empty state
 * and the list of planned capabilities. No sample data is shown.
 */
export default function FeaturePage({ feature }: { feature: FeatureKey }) {
  const def = FEATURES[feature]
  const Icon = def.icon
  const action = 'action' in def ? def.action : undefined

  return (
    <div className="animate-fade-in">
      <PageHeader
        eyebrow={def.eyebrow}
        title={def.title}
        description={def.description}
        action={
          <Badge tone="warning" mono>
            Coming soon
          </Badge>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <SectionCard className="lg:col-span-2" title={def.title} description="Current status" icon={<Icon />}>
          <EmptyState
            icon={<Icon />}
            title={def.emptyTitle}
            description={def.emptyDescription}
            actionLabel={action?.label}
            actionTo={action?.to}
          />
        </SectionCard>

        <SectionCard title="What's planned" description="Arriving in a future phase" icon={<Sparkles />}>
          <ul className="space-y-3">
            {def.planned.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-ink-700">
                <CircleDashed className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  )
}
