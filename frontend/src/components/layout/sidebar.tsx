"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, ChevronDown, CircleHelp, Home, LayoutList, Menu, Plug, Settings, Sparkles, UserRound, X } from "lucide-react";
import { useState } from "react";

const primaryNavigation = [
  { label: "Home", href: "/", icon: Home },
  { label: "Meetings", href: "/meetings", icon: LayoutList },
];
const placeholders = [
  { label: "Tasks", href: "/tasks", icon: UserRound },
  { label: "AskFred", href: "/askfred", icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isMeetings = pathname === "/" || pathname.startsWith("/meetings");
  return <>
    <button onClick={() => setOpen(true)} aria-label="Open navigation" className="fixed left-4 top-4 z-40 rounded-lg border border-slate-200 bg-white p-2 text-slate-600 shadow-sm lg:hidden"><Menu className="h-5 w-5" /></button>
    {open && <button aria-label="Close navigation overlay" onClick={() => setOpen(false)} className="fixed inset-0 z-40 bg-slate-900/20 lg:hidden" />}
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-slate-200 bg-white px-3 py-4 transition-transform lg:static lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="mb-7 flex items-center justify-between px-2"><Link href="/" className="flex items-center gap-2.5" onClick={() => setOpen(false)}><span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">f</span><span className="text-[17px] font-semibold tracking-tight text-slate-900">fireflies.ai</span></Link><button onClick={() => setOpen(false)} aria-label="Close navigation" className="text-slate-400 lg:hidden"><X className="h-5 w-5" /></button></div>
      <button className="mb-6 flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm font-medium text-slate-700"><span className="flex items-center gap-2"><span className="grid h-5 w-5 place-items-center rounded bg-indigo-100 text-[10px] font-bold text-indigo-700">AC</span> Acme workspace</span><ChevronDown className="h-4 w-4 text-slate-400" /></button>
      <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">Workspace</p>
      <nav className="space-y-1" aria-label="Primary navigation">
        {primaryNavigation.map(({ label, href, icon: Icon }) => {
          const active = label === "Meetings" ? isMeetings : pathname === href && !isMeetings;
          return <Link key={label} href={href} onClick={() => setOpen(false)} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${active ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}><Icon className="h-[18px] w-[18px]" />{label}</Link>;
        })}
        {placeholders.map(({ label, href, icon: Icon }) => <Link key={label} href={href} onClick={() => setOpen(false)} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"><Icon className="h-[18px] w-[18px]" />{label}</Link>)}
      </nav>
      <p className="mt-7 px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-400">More</p>
      <div className="space-y-1"><Link href="/integrations" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"><Plug className="h-[18px] w-[18px]" />Integrations</Link><Link href="/settings" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"><Settings className="h-[18px] w-[18px]" />Settings</Link><div className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400" title="Support is not connected"><CircleHelp className="h-[18px] w-[18px]" />Help & support</div></div>
      <div className="mt-auto border-t border-slate-100 pt-4"><div className="flex items-center gap-2.5 rounded-lg px-2 py-2"><span className="grid h-8 w-8 place-items-center rounded-full bg-violet-100 text-xs font-semibold text-violet-700">MC</span><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">Maya Chen</p><p className="truncate text-xs text-slate-400">Acme workspace</p></div><Bot className="ml-auto h-4 w-4 text-slate-400" /></div></div>
    </aside>
  </>;
}
