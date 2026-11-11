export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export async function apiRequest<T>(path: string, signal?: AbortSignal, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError("Unable to connect to the meetings service. Please try again.", 0);
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const detail = isErrorDetail(body) ? body.detail : "The meetings service returned an unexpected error.";
    throw new ApiError(detail, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiUrl(path: string) { return path.startsWith("http") ? path : `${API_URL}${path}`; }

function isErrorDetail(value: unknown): value is { detail: string } {
  return typeof value === "object" && value !== null && "detail" in value && typeof value.detail === "string";
}
