import { CalendarSearch, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

interface EmptyStateProps { filtered: boolean; onReset: () => void; }

export function MeetingEmptyState({ filtered, onReset }: EmptyStateProps) {
  return <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"><div className="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-full bg-indigo-50 text-indigo-600"><CalendarSearch className="h-5 w-5" /></div><h2 className="text-base font-semibold text-slate-800">{filtered ? "No meetings found." : "No meetings yet."}</h2><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">{filtered ? "Try adjusting your search or date filters to find a recorded meeting." : "Once meetings are recorded, they will appear here for your workspace."}</p>{filtered && <Button className="mt-5" onClick={onReset}><RefreshCw className="h-4 w-4" />Clear filters</Button>}</div>;
}
