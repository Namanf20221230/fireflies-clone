import { apiRequest } from "@/lib/api/client";
import type { ActionItem, MeetingDetail, MeetingsQuery, MeetingsResponse, Note, SearchResult, WorkspaceMeeting } from "@/types/meeting";

export function getMeetings(params: MeetingsQuery, signal?: AbortSignal): Promise<MeetingsResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.start_date) query.set("start_date", params.start_date);
  if (params.end_date) query.set("end_date", params.end_date);
  if (params.sort) query.set("sort", params.sort);
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  const suffix = query.size ? `?${query.toString()}` : "";
  return apiRequest<MeetingsResponse>(`/api/v1/meetings${suffix}`, signal);
}

export function getMeetingById(id: string, signal?: AbortSignal): Promise<MeetingDetail> {
  return apiRequest<MeetingDetail>(`/api/v1/meetings/${encodeURIComponent(id)}`, signal);
}
export function getWorkspace(id: string, signal?: AbortSignal): Promise<WorkspaceMeeting> { return apiRequest<WorkspaceMeeting>(`/api/v1/meetings/${id}/workspace`, signal); }
export function patchAction(id: number, body: Partial<ActionItem>): Promise<ActionItem> { return apiRequest<ActionItem>(`/api/v1/action-items/${id}`, undefined, { method: "PATCH", body: JSON.stringify(body) }); }
export function createAction(meetingId: number, body: Pick<ActionItem, "title" | "description" | "priority" | "status">): Promise<ActionItem> { return apiRequest<ActionItem>(`/api/v1/meetings/${meetingId}/action-items`, undefined, { method: "POST", body: JSON.stringify(body) }); }
export function deleteAction(id: number): Promise<void> { return apiRequest<void>(`/api/v1/action-items/${id}`, undefined, { method: "DELETE" }); }
export function createNote(meetingId: number, content: string): Promise<Note> { return apiRequest<Note>(`/api/v1/meetings/${meetingId}/notes`, undefined, { method: "POST", body: JSON.stringify({ content }) }); }
export function patchNote(id: number, content: string): Promise<Note> { return apiRequest<Note>(`/api/v1/notes/${id}`, undefined, { method: "PATCH", body: JSON.stringify({ content }) }); }
export function deleteNote(id: number): Promise<void> { return apiRequest<void>(`/api/v1/notes/${id}`, undefined, { method: "DELETE" }); }
export function searchMeetings(q: string): Promise<{items: SearchResult[]}> { return apiRequest<{items: SearchResult[]}>(`/api/v1/search?q=${encodeURIComponent(q)}`); }
export function askMeeting(meetingId: number, question: string): Promise<{answer: string}> { return apiRequest<{answer: string}>(`/api/v1/meetings/${meetingId}/ask`, undefined, { method: "POST", body: JSON.stringify({ question }) }); }
export function regenerateSummary(meetingId: number) { return apiRequest(`/api/v1/meetings/${meetingId}/summary/generate`, undefined, { method: "POST" }); }
