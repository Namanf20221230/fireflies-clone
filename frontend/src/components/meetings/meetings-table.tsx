import { MeetingRow } from "@/components/meetings/meeting-row";
import type { MeetingListItem } from "@/types/meeting";

export function MeetingsTable({ meetings }: { meetings: MeetingListItem[] }) {
  return <div className="overflow-hidden rounded-xl border border-slate-200 bg-white"><div className="hidden grid-cols-[minmax(250px,2fr)_130px_170px_90px] gap-4 border-b border-slate-200 bg-slate-50 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.07em] text-slate-400 lg:grid"><span>Meeting</span><span>Participants</span><span>Date</span><span>Duration</span></div>{meetings.map((meeting) => <MeetingRow key={meeting.id} meeting={meeting} />)}</div>;
}
