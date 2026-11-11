interface BadgeProps { label: string; color?: string; }

export function Badge({ label, color }: BadgeProps) {
  return <span className="inline-flex items-center rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-600"><span className="mr-1.5 h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color ?? "#94a3b8" }} />{label}</span>;
}
