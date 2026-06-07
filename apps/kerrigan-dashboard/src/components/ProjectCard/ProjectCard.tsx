import type { PortfolioCardData } from "../../lib/portfolio.js";

interface ProjectCardProps {
  card: PortfolioCardData;
}

function displayValue(value: string | null): string {
  return value ?? "—";
}

function attentionClass(value: number): string {
  return value > 0 ? "text-accent" : "text-[#A2AAB8]";
}

export function ProjectCard({ card }: ProjectCardProps) {
  return (
    <article
      className="rounded-lg border border-[#1E2530] bg-[#101724] p-5"
      data-testid={`project-card-${card.id}`}
    >
      <header className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-heading font-semibold text-neutral-fg">{card.name}</h2>
        <span
          className={`rounded border border-[#2A3342] px-2 py-1 text-nano ${attentionClass(card.blockCount)}`}
        >
          {card.blockCount} block{card.blockCount === 1 ? "" : "s"}
        </span>
      </header>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-micro">
        <Field label="Repos" value={String(card.repoCount)} />
        <Field label="Current wave" value={displayValue(card.currentWave)} />
        <Field
          label="Blocked"
          value={String(card.blockCount)}
          valueClassName={attentionClass(card.blockCount)}
          valueTestId="blocked-value"
        />
        <Field
          label="Interventions"
          value={String(card.interventionCount)}
          valueClassName={attentionClass(card.interventionCount)}
          valueTestId="intervention-value"
        />
        <Field
          label="Last PR merged"
          value={displayValue(card.lastPrMergedAt)}
          valueTestId="last-pr-merged-value"
        />
      </dl>
    </article>
  );
}

interface FieldProps {
  label: string;
  value: string;
  valueClassName?: string;
  valueTestId?: string;
}

function Field({ label, value, valueClassName, valueTestId }: FieldProps) {
  return (
    <div className="space-y-1">
      <dt className="text-nano uppercase tracking-[0.05em] text-[#8B94A6]">{label}</dt>
      <dd
        className={`text-body font-medium text-neutral-fg ${valueClassName ?? ""}`.trim()}
        data-testid={valueTestId}
      >
        {value}
      </dd>
    </div>
  );
}
