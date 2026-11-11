"use client";

import { X } from "lucide-react";

interface ToastProps { message: string; onDismiss: () => void; }

export function Toast({ message, onDismiss }: ToastProps) {
  return <div role="status" className="fixed bottom-5 right-5 z-50 flex max-w-sm items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-lg"><span>{message}</span><button onClick={onDismiss} aria-label="Dismiss notification" className="text-slate-400 hover:text-slate-700"><X className="h-4 w-4" /></button></div>;
}
