"use client";

import { Pause, Play, Volume2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { apiUrl } from "@/lib/api/client";

export function AudioPlayer({ recordingUrl, seekMs, onTimeChange }: { recordingUrl: string | null; seekMs: number | null; onTimeChange: (milliseconds: number) => void }) {
  const audio = useRef<HTMLAudioElement>(null); const [playing, setPlaying] = useState(false); const [current, setCurrent] = useState(0); const [duration, setDuration] = useState(0);
  useEffect(() => { if (seekMs !== null && audio.current) { audio.current.currentTime = seekMs / 1000; void audio.current.play().then(() => setPlaying(true)).catch(() => undefined); } }, [seekMs]);
  if (!recordingUrl) return <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">No recording is available for this seeded meeting. Upload a recording to enable real HTML5 playback and timestamp seeking.</div>;
  const clock = (value: number) => `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, "0")}`;
  const toggle = () => { const player = audio.current; if (!player) return; if (player.paused) void player.play().then(() => setPlaying(true)); else { player.pause(); setPlaying(false); } };
  return <div className="rounded-xl bg-slate-900 p-4 text-white"><audio ref={audio} src={apiUrl(recordingUrl)} onTimeUpdate={(event) => { setCurrent(event.currentTarget.currentTime); onTimeChange(event.currentTarget.currentTime * 1000); }} onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)} onEnded={() => setPlaying(false)} /><div className="flex items-center gap-3"><button aria-label={playing ? "Pause recording" : "Play recording"} onClick={toggle} className="rounded-full bg-indigo-500 p-2.5 hover:bg-indigo-400">{playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}</button><span className="w-20 text-xs tabular-nums">{clock(current)} / {clock(duration || 0)}</span><input aria-label="Recording progress" className="h-1 flex-1 accent-indigo-400" type="range" min="0" max={duration || 0} step="0.1" value={current} onChange={(event) => { if (audio.current) audio.current.currentTime = Number(event.target.value); }} /><Volume2 className="h-4 w-4 text-slate-300" /><select aria-label="Playback speed" onChange={(event) => { if (audio.current) audio.current.playbackRate = Number(event.target.value); }} className="rounded bg-slate-800 px-2 py-1 text-xs"><option value="0.75">0.75×</option><option value="1">1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></div></div>;
}
