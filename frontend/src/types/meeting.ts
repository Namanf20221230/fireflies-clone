export type SortOrder = "newest" | "oldest";

export interface Participant {
  id: number;
  name: string;
  email: string | null;
  avatar_url: string | null;
}

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface MeetingListItem {
  id: number;
  title: string;
  description: string;
  meeting_date: string;
  duration_seconds: number;
  participants: Participant[];
  participant_count: number;
  tags: Tag[];
  summary_preview: string | null;
}

export interface MeetingDetail extends MeetingListItem {
  recording_url: string | null;
  recording_type: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}
export interface TranscriptSegment { id: number; meeting_id: number; participant_id: number | null; start_time_ms: number; end_time_ms: number; text: string; sequence_number: number; participant: Participant | null; }
export interface MeetingSummary { id: number; meeting_id: number; overview: string; key_points: Record<string, unknown>[]; decisions: Record<string, unknown>[]; generated_by: string; created_at: string; updated_at: string; }
export interface ActionItem { id: number; meeting_id: number; title: string; description: string; assignee_id: number | null; due_date: string | null; priority: string; status: string; created_at: string; updated_at: string; }
export interface Chapter { id: number; meeting_id: number; title: string; description: string; start_time_ms: number; end_time_ms: number; sequence_number: number; }
export interface Note { id: number; meeting_id: number; content: string; created_at: string; updated_at: string; }
export interface WorkspaceMeeting extends MeetingDetail { summary: MeetingSummary | null; transcript_segments: TranscriptSegment[]; action_items: ActionItem[]; chapters: Chapter[]; notes: Note[]; }
export interface SearchResult { meeting: MeetingListItem; match_type: "meeting" | "participant" | "tag" | "transcript"; snippet: string | null; timestamp_ms: number | null; }

export interface MeetingsResponse {
  items: MeetingListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MeetingsQuery {
  search?: string;
  start_date?: string;
  end_date?: string;
  sort?: SortOrder;
  page?: number;
  page_size?: number;
}
