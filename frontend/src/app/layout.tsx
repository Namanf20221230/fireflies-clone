import type { Metadata } from "next";
import { Suspense } from "react";
import { AppShell } from "@/components/layout/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fireflies Clone",
  description: "Meeting intelligence platform",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full"><Suspense fallback={<main className="min-h-screen bg-slate-50" />}><AppShell>{children}</AppShell></Suspense></body>
    </html>
  );
}
