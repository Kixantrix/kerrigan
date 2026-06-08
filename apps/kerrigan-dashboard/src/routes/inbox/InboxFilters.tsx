import {
  INITIAL_FILTER_STATE,
  type AgeFilter,
  type InboxFilterState,
  type KindFilter,
} from "./inboxFilterUtils.js";

interface InboxFiltersProps {
  projects: ReadonlyArray<string>;
  filters: InboxFilterState;
  onChange: (filters: InboxFilterState) => void;
  totalCount: number;
  filteredCount: number;
}

const KIND_OPTIONS: ReadonlyArray<{ value: KindFilter; label: string }> = [
  { value: "all", label: "All types" },
  { value: "block", label: "Blocks" },
  { value: "capture-issue", label: "Captures" },
  { value: "review", label: "Reviews" },
  { value: "attestation", label: "Attestations" },
];

const AGE_OPTIONS: ReadonlyArray<{ value: AgeFilter; label: string }> = [
  { value: "all", label: "Any age" },
  { value: ">1d", label: ">1 day" },
  { value: ">7d", label: ">7 days" },
  { value: ">30d", label: ">30 days" },
];

export function InboxFilters({
  projects,
  filters,
  onChange,
  totalCount,
  filteredCount,
}: InboxFiltersProps) {
  function handleProjectChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const value = event.target.value;
    onChange({ ...filters, projectId: value === "" ? null : value });
  }

  function handleKindChange(event: React.ChangeEvent<HTMLSelectElement>) {
    onChange({ ...filters, kind: event.target.value as KindFilter });
  }

  function handleAgeChange(event: React.ChangeEvent<HTMLSelectElement>) {
    onChange({ ...filters, age: event.target.value as AgeFilter });
  }

  function handleReset() {
    onChange(INITIAL_FILTER_STATE);
  }

  const isFiltered =
    filters.projectId !== null || filters.kind !== "all" || filters.age !== "all";

  return (
    <div className="flex flex-wrap items-center gap-3" data-testid="inbox-filters">
      <select
        value={filters.projectId ?? ""}
        onChange={handleProjectChange}
        className="rounded border border-[#2A3342] bg-[#0D1117] px-2 py-1 text-micro text-neutral-fg focus:border-brand focus:outline-none"
        data-testid="inbox-filter-project"
        aria-label="Filter by project"
      >
        <option value="">All projects</option>
        {projects.map((projectId) => (
          <option key={projectId} value={projectId}>
            {projectId}
          </option>
        ))}
      </select>

      <select
        value={filters.kind}
        onChange={handleKindChange}
        className="rounded border border-[#2A3342] bg-[#0D1117] px-2 py-1 text-micro text-neutral-fg focus:border-brand focus:outline-none"
        data-testid="inbox-filter-kind"
        aria-label="Filter by type"
      >
        {KIND_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <select
        value={filters.age}
        onChange={handleAgeChange}
        className="rounded border border-[#2A3342] bg-[#0D1117] px-2 py-1 text-micro text-neutral-fg focus:border-brand focus:outline-none"
        data-testid="inbox-filter-age"
        aria-label="Filter by age"
      >
        {AGE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {isFiltered && (
        <button
          type="button"
          onClick={handleReset}
          className="text-micro text-[#8B94A6] hover:text-neutral-fg"
          data-testid="inbox-filter-reset"
        >
          Reset
        </button>
      )}

      <span className="ml-auto text-micro text-[#8B94A6]" data-testid="inbox-filter-count">
        {isFiltered ? `${filteredCount} of ${totalCount}` : `${totalCount}`}{" "}
        {totalCount === 1 ? "item" : "items"}
      </span>
    </div>
  );
}
