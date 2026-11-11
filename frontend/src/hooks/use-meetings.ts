"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { getMeetings } from "@/lib/api/meetings";
import type { MeetingsQuery, MeetingsResponse } from "@/types/meeting";

interface MeetingsState {
  requestKey: string;
  data: MeetingsResponse | null;
  error: string | null;
}

export function useMeetings(query: MeetingsQuery) {
  const [state, setState] = useState<MeetingsState>({ requestKey: "", data: null, error: null });
  const [refreshToken, setRefreshToken] = useState(0);
  const queryKey = useMemo(() => JSON.stringify(query), [query]);
  const stableQuery = useMemo(() => JSON.parse(queryKey) as MeetingsQuery, [queryKey]);
  const requestKey = `${queryKey}:${refreshToken}`;

  useEffect(() => {
    const controller = new AbortController();
    getMeetings(stableQuery, controller.signal)
      .then((data) => setState({ requestKey, data, error: null }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof ApiError ? error.message : "Unable to load meetings.";
        setState({ requestKey, data: null, error: message });
      });
    return () => controller.abort();
  }, [requestKey, stableQuery]);

  const refresh = useCallback(() => setRefreshToken((value) => value + 1), []);
  return {
    data: state.requestKey === requestKey ? state.data : null,
    error: state.requestKey === requestKey ? state.error : null,
    loading: state.requestKey !== requestKey,
    refresh,
  };
}
