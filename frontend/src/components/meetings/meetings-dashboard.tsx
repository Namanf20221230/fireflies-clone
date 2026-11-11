"use client";

import { Search, SlidersHorizontal, Upload, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MeetingEmptyState } from "@/components/meetings/meeting-empty-state";
import { MeetingListSkeleton } from "@/components/meetings/meeting-list-skeleton";
import { MeetingPagination } from "@/components/meetings/meeting-pagination";
import { MeetingsTable } from "@/components/meetings/meetings-table";
import { Button } from "@/components/ui/button";
import { Toast } from "@/components/ui/toast";
import { useDebounce } from "@/hooks/use-debounce";
import { useMeetings } from "@/hooks/use-meetings";
import type { MeetingsQuery, SortOrder } from "@/types/meeting";

const PAGE_SIZE = 10;

function positiveInteger(value: string | null, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export function MeetingsDashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeSearch = searchParams.get("search") ?? "";
  const sort: SortOrder = searchParams.get("sort") === "oldest" ? "oldest" : "newest";
  const page = positiveInteger(searchParams.get("page"), 1);
  const [searchInput, setSearchInput] = useState(activeSearch);
  const [startDate, setStartDate] = useState(searchParams.get("start_date") ?? "");
  const [endDate, setEndDate] = useState(searchParams.get("end_date") ?? "");
  const [dateError, setDateError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const debouncedSearch = useDebounce(searchInput.trim());

  const updateUrl = useCallback((updates: Record<string, string | undefined>) => {
    const next = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([key, value]) => value ? next.set(key, value) : next.delete(key));
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }, [pathname, router, searchParams]);

  useEffect(() => {
    if (debouncedSearch !== activeSearch) updateUrl({ search: debouncedSearch || undefined, page: "1" });
  }, [activeSearch, debouncedSearch, updateUrl]);

  const query = useMemo<MeetingsQuery>(() => ({
    search: activeSearch || undefined,
    start_date: searchParams.get("start_date") ?? undefined,
    end_date: searchParams.get("end_date") ?? undefined,
    sort,
    page,
    page_size: PAGE_SIZE,
  }), [activeSearch, page, searchParams, sort]);
  const { data, loading, error, refresh } = useMeetings(query);
  const filtered = Boolean(activeSearch || startDate || endDate || sort !== "newest");

  const applyDates = () => {
    if (startDate && endDate && startDate > endDate) {
      setDateError("Start date must be on or before end date.");
      return;
    }
    setDateError(null);
    updateUrl({ start_date: startDate || undefined, end_date: endDate || undefined, page: "1" });
  };
  const reset = () => {
    setSearchInput(""); setStartDate(""); setEndDate(""); setDateError(null);
    router.replace(pathname, { scroll: false }); setToast("Filters cleared.");
  };

  return <div className="mx-auto w-full max-w-[1440px] px-5 py-7 sm:px-8 lg:px-10">
    <div className="flex flex-col gap-5 border-b border-slate-200 pb-6 sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-1 text-sm font-medium text-indigo-600">Workspace library</p><h1 className="text-2xl font-semibold tracking-tight text-slate-900">Meetings</h1><p className="mt-1 text-sm text-slate-500">Review, search and manage your recorded meetings.</p></div><Link href="/upload" className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 text-sm font-medium text-white hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"><Upload className="h-4 w-4" />Upload transcript</Link></div>
    <section className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm" aria-label="Meeting filters"><div className="flex flex-col gap-3 xl:flex-row xl:items-center"><div className="relative min-w-0 flex-1"><label htmlFor="meeting-search" className="sr-only">Search meetings or participants</label><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input id="meeting-search" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Search meetings or participants…" className="h-10 w-full rounded-lg border border-slate-200 pl-9 pr-9 text-sm text-slate-800 outline-none transition focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" />{searchInput && <button aria-label="Clear search" onClick={() => setSearchInput("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"><X className="h-4 w-4" /></button>}</div><div className="flex flex-col gap-2 sm:flex-row"><label className="sr-only" htmlFor="start-date">Start date</label><input id="start-date" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="h-10 rounded-lg border border-slate-200 px-3 text-sm text-slate-600 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" /><label className="sr-only" htmlFor="end-date">End date</label><input id="end-date" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="h-10 rounded-lg border border-slate-200 px-3 text-sm text-slate-600 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" /><Button onClick={applyDates}><SlidersHorizontal className="h-4 w-4" />Apply</Button></div><label className="sr-only" htmlFor="meeting-sort">Sort meetings</label><select id="meeting-sort" value={sort} onChange={(event) => updateUrl({ sort: event.target.value, page: "1" })} className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"><option value="newest">Newest first</option><option value="oldest">Oldest first</option></select>{filtered && <Button variant="ghost" onClick={reset}>Reset</Button>}</div>{dateError && <p role="alert" className="mt-2 text-xs font-medium text-rose-600">{dateError}</p>}</section>
    <section className="mt-6" aria-live="polite">{loading && <MeetingListSkeleton />}{!loading && error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-5 py-7 text-center"><h2 className="font-semibold text-rose-800">Couldn&apos;t load meetings</h2><p className="mt-1 text-sm text-rose-700">{error}</p><Button className="mt-4" onClick={refresh}>Try again</Button></div>}{!loading && !error && data && (data.items.length ? <><MeetingsTable meetings={data.items} /><MeetingPagination page={data.page} totalPages={data.total_pages} total={data.total} onPageChange={(nextPage) => updateUrl({ page: String(nextPage) })} /></> : <MeetingEmptyState filtered={filtered} onReset={reset} />)}</section>
    {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}
  </div>;
}
