import type { Participant } from "@/types/meeting";

interface AvatarProps {
  participant: Participant;
  size?: "sm" | "md";
}

export function Avatar({ participant, size = "sm" }: AvatarProps) {
  const initials = participant.name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const dimensions = size === "sm" ? "h-8 w-8 text-[10px]" : "h-10 w-10 text-xs";
  if (participant.avatar_url) {
    return <Image className={`${dimensions} rounded-full border-2 border-white object-cover`} src={participant.avatar_url} alt={participant.name} title={participant.name} width={40} height={40} />;
  }
  return <span className={`${dimensions} inline-flex items-center justify-center rounded-full border-2 border-white bg-indigo-100 font-semibold text-indigo-700`} title={participant.name}>{initials}</span>;
}
import Image from "next/image";
