import { Suspense } from "react";

import { MeetingsDashboard } from "@/components/meetings/meetings-dashboard";

export default function MeetingsPage() {
  return <Suspense fallback={null}><MeetingsDashboard /></Suspense>;
}
