import { Bell } from "lucide-react";

export function Header() {
  return <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5 pl-16 lg:px-8"><div><p className="text-xs font-medium text-slate-400">Acme workspace</p><p className="text-sm font-semibold text-slate-800">Meetings</p></div><div className="flex items-center gap-4"><button aria-label="Notifications are coming soon" title="Notifications are coming soon" className="rounded-lg p-2 text-slate-400 hover:bg-slate-50 hover:text-slate-600"><Bell className="h-5 w-5" /></button><span className="grid h-8 w-8 place-items-center rounded-full bg-violet-100 text-xs font-semibold text-violet-700">MC</span></div></header>;
}
