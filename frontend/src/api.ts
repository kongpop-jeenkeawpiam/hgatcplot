import { fallbackGroups } from "./fallbackModules";
import type { JobResult, PlotModule, PrecheckResult } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchModules(): Promise<Record<string, PlotModule[]>> {
  try {
    const payload = await json<{ groups: Record<string, PlotModule[]> }>("/api/modules");
    return payload.groups;
  } catch {
    return fallbackGroups;
  }
}

export async function precheck(moduleSlug: string, data: string, source: "paste" | "upload" | "demo"): Promise<PrecheckResult> {
  return json<PrecheckResult>(`/api/modules/${moduleSlug}/precheck`, {
    method: "POST",
    body: JSON.stringify({ data, source })
  });
}

export async function createJob(moduleSlug: string, data: string, options: Record<string, string | number>, sessionId: string): Promise<JobResult> {
  return json<JobResult>("/api/jobs", {
    method: "POST",
    body: JSON.stringify({ moduleSlug, data, options, sessionId })
  });
}

export async function fetchHistory(sessionId: string): Promise<JobResult[]> {
  try {
    const payload = await json<{ jobs: JobResult[] }>(`/api/history?sessionId=${encodeURIComponent(sessionId)}`);
    return payload.jobs;
  } catch {
    return [];
  }
}

export function artifactHref(path?: string): string {
  if (!path) return "#";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

