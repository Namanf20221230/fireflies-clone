import Link from "next/link";
import { CalendarDays, Clock3 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ParticipantAvatars } from "@/components/meetings/participant-avatars";
import { formatMeetingDate } from "@/lib/utils/date";
import { formatDuration } from "@/lib/utils/duration";
import type { MeetingListItem } from "@/types/meeting";

export function MeetingRow({ meeting }: { meeting: MeetingListItem }) {
  return <Link href={`/meetings/${meeting.id}`} className="group grid gap-4 border-b border-slate-100 px-5 py-4 transition-colors hover:bg-slate-50 focus-visible:z-10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500 lg:grid-cols-[minmax(250px,2fr)_130px_170px_90px] lg:items-center"><div className="min-w-0"><div className="flex items-center gap-2"><h2 className="truncate text-sm font-semibold text-slate-800 group-hover:text-indigo-700">{meeting.title}</h2></div><p className="mt-1 line-clamp-1 text-xs leading-5 text-slate-500">{meeting.summary_preview ?? meeting.description}</p><div className="mt-2 flex flex-wrap gap-1.5">{meeting.tags.map((tag) => <Badge key={tag.id} label={tag.name} color={tag.color} />)}</div></div><div className="flex items-center gap-2"><ParticipantAvatars participants={meeting.participants} /><span className="text-xs text-slate-400">{meeting.participant_count}</span></div><div className="flex items-center gap-1.5 text-xs text-slate-500"><CalendarDays className="h-3.5 w-3.5 text-slate-400" />{formatMeetingDate(meeting.meeting_date)}</div><div className="flex items-center gap-1.5 text-xs text-slate-500"><Clock3 className="h-3.5 w-3.5 text-slate-400" />{formatDuration(meeting.duration_seconds)}</div></Link>;
}
