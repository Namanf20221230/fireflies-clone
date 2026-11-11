import { Construction } from "lucide-react";

export function PlaceholderScreen({ title, description }: { title: string; description: string }) {
  return <main className="mx-auto max-w-3xl px-6 py-12"><section className="rounded-xl border border-slate-200 bg-white p-8"><Construction className="h-6 w-6 text-indigo-600" /><h1 className="mt-4 text-2xl font-semibold text-slate-900">{title}</h1><p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">{description}</p><p className="mt-5 text-xs font-medium uppercase tracking-wider text-slate-400">No authentication or third-party connection is configured in this demo.</p></section></main>;
}
