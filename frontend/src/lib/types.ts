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

export interface TimelineGroup {
	month: string;
	label: string;
	entries: Entry[];
	count: number;
}

export interface TimelineResponse {
	groups: TimelineGroup[];
	total: number;
}

export interface PlaceCount {
	name: string;
	count: number;
}

export interface GraphNode {
	node_type: 'person' | 'topic' | 'place';
	node_id: string;
	label: string;
	entry_count: number;
	first_date: string | null;
	last_date: string | null;
}

export interface GraphEdge {
	source_type: string;
	source_id: string;
	target_type: string;
	target_id: string;
	weight: number;
	first_date: string | null;
	last_date: string | null;
}

export interface GraphData {
	nodes: GraphNode[];
	edges: GraphEdge[];
}

export interface MapPoint {
	uuid: string;
	latitude: number;
	longitude: number;
	creation_date: string;
	snippet: string | null;
	place_name: string | null;
	photo_id: number | null;
}

export interface ReportStatus {
	id: string;
	status: 'generating' | 'done' | 'error';
	progress: number;
	message: string;
	person_name: string | null;
}
