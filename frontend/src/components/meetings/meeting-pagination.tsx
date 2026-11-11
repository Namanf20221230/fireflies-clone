import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface PaginationProps { page: number; totalPages: number; total: number; onPageChange: (page: number) => void; }

export function MeetingPagination({ page, totalPages, total, onPageChange }: PaginationProps) {
  if (total === 0) return null;
  return <div className="mt-5 flex flex-col gap-3 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between"><p>{total} meeting{total === 1 ? "" : "s"} total</p><div className="flex items-center gap-2"><Button variant="secondary" onClick={() => onPageChange(page - 1)} disabled={page <= 1}><ChevronLeft className="h-4 w-4" />Previous</Button><span className="px-2 text-xs font-medium text-slate-500">Page {page} of {Math.max(totalPages, 1)}</span><Button variant="secondary" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}><span className="hidden sm:inline">Next</span><ChevronRight className="h-4 w-4" /></Button></div></div>;
}
