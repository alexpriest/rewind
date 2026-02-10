import { writable } from 'svelte/store';

export interface Filters {
	query: string;
	people: string[];
	places: string[];
	tags: string[];
	dateFrom: string;
	dateTo: string;
}

export const filters = writable<Filters>({
	query: '',
	people: [],
	places: [],
	tags: [],
	dateFrom: '',
	dateTo: ''
});

export function resetFilters() {
	filters.set({
		query: '',
		people: [],
		places: [],
		tags: [],
		dateFrom: '',
		dateTo: ''
	});
}
