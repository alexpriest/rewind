export interface Entry {
	uuid: string;
	creation_date: string;
	text: string | null;
	snippet: string | null;
	starred: boolean;
	latitude: number | null;
	longitude: number | null;
	place_name: string | null;
	locality: string | null;
	admin_area: string | null;
	country: string | null;
	weather_description: string | null;
	weather_temp_c: number | null;
	word_count: number | null;
	tags: string[];
	photos: Photo[];
}

export interface Photo {
	id: number;
	identifier: string;
	file_type: string | null;
	has_thumbnail: boolean;
}

export interface Tag {
	id: number;
	name: string;
	tag_type: 'person' | 'topic';
	ai_suggested_type: string | null;
	user_confirmed: boolean;
	entry_count: number;
}

export interface EntryListResponse {
	entries: Entry[];
	total: number;
	page: number;
	page_size: number;
}

export interface ImportStatus {
	id: string;
	status:
		| 'uploading'
		| 'parsing'
		| 'importing'
		| 'classifying'
		| 'computing_graph'
		| 'done'
		| 'error';
	progress: number;
	message: string;
	entry_count: number | null;
	tag_count: number | null;
	photo_count: number | null;
}

export interface GraphNode {
	id: string;
	type: 'person' | 'topic' | 'place';
	label: string;
	entry_count: number;
}

export interface GraphEdge {
	source: string;
	target: string;
	weight: number;
}

export interface GraphData {
	nodes: GraphNode[];
	edges: GraphEdge[];
}
