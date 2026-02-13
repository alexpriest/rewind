import type { EntryListResponse, Entry, Tag, ImportStatus, TimelineResponse, PlaceCount, GraphData, MapPoint, ReportStatus } from './types';

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
	const res = await fetch(url, init);
	if (!res.ok) {
		const text = await res.text();
		throw new Error(`${res.status}: ${text}`);
	}
	return res.json();
}

export async function getEntries(
	params: {
		page?: number;
		page_size?: number;
		q?: string;
		tag?: string;
		place?: string;
		date_from?: string;
		date_to?: string;
	} = {}
): Promise<EntryListResponse> {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') {
			searchParams.set(key, String(value));
		}
	}
	return fetchJSON(`/api/entries?${searchParams}`);
}

export async function getEntry(uuid: string): Promise<Entry> {
	return fetchJSON(`/api/entries/${uuid}`);
}

export async function getTags(): Promise<Tag[]> {
	return fetchJSON('/api/tags');
}

export async function updateTag(id: number, tag_type: string): Promise<Tag> {
	return fetchJSON(`/api/tags/${id}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tag_type })
	});
}

export async function uploadJournal(file: File): Promise<ImportStatus> {
	const formData = new FormData();
	formData.append('file', file);
	return fetchJSON('/api/import/upload', {
		method: 'POST',
		body: formData
	});
}

export async function getImportStatus(importId: string): Promise<ImportStatus> {
	return fetchJSON(`/api/import/status/${importId}`);
}

export async function getTimeline(
	params: { q?: string; tag?: string; place?: string; date_from?: string; date_to?: string; limit?: number } = {}
): Promise<TimelineResponse> {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') {
			searchParams.set(key, String(value));
		}
	}
	return fetchJSON(`/api/entries/timeline?${searchParams}`);
}

export async function getPlaces(): Promise<PlaceCount[]> {
	return fetchJSON('/api/entries/places');
}

export async function healthCheck(): Promise<{ status: string }> {
	return fetchJSON('/api/health');
}

export async function getGraph(
	params: {
		types?: string;
		date_from?: string;
		date_to?: string;
		min_weight?: number;
	} = {}
): Promise<GraphData> {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') {
			searchParams.set(key, String(value));
		}
	}
	return fetchJSON(`/api/graph?${searchParams}`);
}

export async function getNodeEntries(nodeType: string, nodeId: string): Promise<Entry[]> {
	return fetchJSON(`/api/graph/node/${encodeURIComponent(nodeType)}/${encodeURIComponent(nodeId)}/entries`);
}

export async function classifyTags(): Promise<Tag[]> {
	return fetchJSON('/api/tags/classify', { method: 'POST' });
}

export async function bulkConfirmTags(tagIds: number[]): Promise<Tag[]> {
	return fetchJSON('/api/tags/bulk-confirm', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ tag_ids: tagIds })
	});
}

export async function getMapPoints(
	params: { q?: string; tag?: string; place?: string; date_from?: string; date_to?: string } = {}
): Promise<MapPoint[]> {
	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') {
			searchParams.set(key, String(value));
		}
	}
	return fetchJSON(`/api/entries/map-points?${searchParams}`);
}

export async function generateReport(params: {
	person_tag_id: number;
	date_from?: string;
	date_to?: string;
}): Promise<ReportStatus> {
	return fetchJSON('/api/reports/generate', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(params)
	});
}

export async function getReportStatus(reportId: string): Promise<ReportStatus> {
	return fetchJSON(`/api/reports/${reportId}/status`);
}
