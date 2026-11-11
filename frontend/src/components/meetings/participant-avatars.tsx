import { Avatar } from "@/components/ui/avatar";
import type { Participant } from "@/types/meeting";

export function ParticipantAvatars({ participants }: { participants: Participant[] }) {
  const visible = participants.slice(0, 3);
  const remaining = participants.length - visible.length;
  return <div className="flex items-center" aria-label={participants.map((person) => person.name).join(", ")}>
    {visible.map((participant, index) => <span key={participant.id} className={index ? "-ml-2" : ""}><Avatar participant={participant} /></span>)}
    {remaining > 0 && <span className="-ml-2 inline-flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-slate-200 text-[10px] font-semibold text-slate-600">+{remaining}</span>}
  </div>;
}
