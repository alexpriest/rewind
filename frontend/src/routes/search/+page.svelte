<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntries, getTimeline, getMapPoints } from '$lib/api';
	import type { EntryListResponse, TimelineResponse, MapPoint } from '$lib/types';
	import EntryCard from '$lib/components/EntryCard.svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';
	import FilterChips from '$lib/components/FilterChips.svelte';
	import MapView from '$lib/components/MapView.svelte';

	type ViewTab = 'timeline' | 'list' | 'map';

	let activeTab: ViewTab = $state('timeline');
	let loading = $state(true);
	let error: string | null = $state(null);

	// Filters
	let query = $state('');
	let tag = $state('');
	let place = $state('');
	let dateFrom = $state('');
	let dateTo = $state('');
	let initialTag = $state('');

	// List state
	let listData = $state<EntryListResponse | null>(null);
	let currentPage = $state(1);
	const pageSize = 20;
	const totalPages = $derived(listData ? Math.ceil(listData.total / pageSize) : 0);

	// Timeline state
	let timelineData = $state<TimelineResponse | null>(null);
	let timelineLimit = $state(50);

	// Map state
	let mapPoints = $state<MapPoint[]>([]);

	function filterParams() {
		return {
			q: query || undefined,
			tag: tag || undefined,
			place: place || undefined,
			date_from: dateFrom || undefined,
			date_to: dateTo || undefined
		};
	}

	async function loadTimeline() {
		loading = true;
		error = null;
		try {
			timelineData = await getTimeline({ ...filterParams(), limit: timelineLimit });
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load timeline';
		} finally {
			loading = false;
		}
	}

	async function loadList() {
		loading = true;
		error = null;
		try {
			listData = await getEntries({
				page: currentPage,
				page_size: pageSize,
				...filterParams()
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load entries';
		} finally {
			loading = false;
		}
	}

	async function loadMap() {
		loading = true;
		error = null;
		try {
			mapPoints = await getMapPoints(filterParams());
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load map data';
		} finally {
			loading = false;
		}
	}

	function load() {
		if (activeTab === 'timeline') loadTimeline();
		else if (activeTab === 'map') loadMap();
		else loadList();
	}

	function handleFilterChange(filters: {
		query: string;
		tag: string;
		place: string;
		dateFrom: string;
		dateTo: string;
	}) {
		query = filters.query;
		tag = filters.tag;
		place = filters.place;
		dateFrom = filters.dateFrom;
		dateTo = filters.dateTo;
		currentPage = 1;
		timelineLimit = 50;
		load();
	}

	function clearFilter(name: string) {
		if (name === 'query') query = '';
		else if (name === 'tag') tag = '';
		else if (name === 'place') place = '';
		else if (name === 'dateFrom') dateFrom = '';
		else if (name === 'dateTo') dateTo = '';
		currentPage = 1;
		timelineLimit = 50;
		load();
	}

	function clearAllFilters() {
		query = '';
		tag = '';
		place = '';
		dateFrom = '';
		dateTo = '';
		currentPage = 1;
		timelineLimit = 50;
		load();
	}

	function switchTab(tab: ViewTab) {
		if (tab === activeTab) return;
		activeTab = tab;
		currentPage = 1;
		timelineLimit = 50;
		load();
	}

	function prevPage() {
		if (currentPage > 1) {
			currentPage--;
			loadList();
		}
	}

	function nextPage() {
		if (listData && currentPage * pageSize < listData.total) {
			currentPage++;
			loadList();
		}
	}

	function loadMoreTimeline() {
		timelineLimit += 50;
		loadTimeline();
	}

	const resultCount = $derived(
		activeTab === 'timeline'
			? timelineData?.total ?? 0
			: activeTab === 'map'
				? mapPoints.length
				: listData?.total ?? 0
	);

	const hasMoreTimeline = $derived(
		timelineData !== null &&
			timelineData.groups.reduce((sum: number, g) => sum + g.entries.length, 0) < timelineData.total
	);

	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const urlTag = params.get('tag');
		if (urlTag) {
			tag = urlTag;
			initialTag = urlTag;
		}
		load();
	});
</script>

<div class="search-page">
	<h1 class="page-title">Entries</h1>

	<SearchBar
		onfilterchange={handleFilterChange}
		initialQuery={query}
		{initialTag}
	/>

	<FilterChips
		{query}
		{tag}
		{place}
		{dateFrom}
		{dateTo}
		onclear={clearFilter}
		onclearall={clearAllFilters}
	/>

	<div class="controls-row">
		<div class="tab-toggle">
			<button
				class="tab-button"
				class:active={activeTab === 'timeline'}
				onclick={() => switchTab('timeline')}
			>
				Timeline
			</button>
			<button
				class="tab-button"
				class:active={activeTab === 'list'}
				onclick={() => switchTab('list')}
			>
				List
			</button>
			<button
				class="tab-button"
				class:active={activeTab === 'map'}
				onclick={() => switchTab('map')}
			>
				Map
			</button>
		</div>
		{#if !loading && resultCount > 0}
			<p class="result-count">
				{resultCount.toLocaleString()} {resultCount === 1 ? 'entry' : 'entries'}
			</p>
		{/if}
	</div>

	{#if loading}
		<div class="loading">
			<p class="loading-text">Loading entries...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button class="retry-button" onclick={load}>Retry</button>
		</div>
	{:else if activeTab === 'timeline'}
		{#if timelineData && timelineData.groups.length > 0}
			<div class="timeline">
				{#each timelineData.groups as group (group.month)}
					<section class="timeline-group">
						<h2 class="month-header">
							{group.label}
							<span class="month-count">
								&mdash; {group.count} {group.count === 1 ? 'entry' : 'entries'}
							</span>
						</h2>
						<div class="entries-list">
							{#each group.entries as entry (entry.uuid)}
								<EntryCard {entry} />
							{/each}
						</div>
					</section>
				{/each}

				{#if hasMoreTimeline}
					<div class="load-more">
						<button class="load-more-button" onclick={loadMoreTimeline}>
							Load more entries
						</button>
					</div>
				{/if}
			</div>
		{:else}
			<div class="empty-state">
				<p class="empty-text">No entries found.</p>
				{#if query || tag || place || dateFrom || dateTo}
					<p class="empty-hint">Try adjusting your filters.</p>
				{:else}
					<p class="empty-hint">
						<a href="/import">Import your journal</a> to get started.
					</p>
				{/if}
			</div>
		{/if}
	{:else if activeTab === 'map'}
		{#if mapPoints.length > 0}
			<MapView points={mapPoints} />
		{:else}
			<div class="empty-state">
				<p class="empty-text">No entries with GPS coordinates found.</p>
				{#if query || tag || place || dateFrom || dateTo}
					<p class="empty-hint">Try adjusting your filters.</p>
				{:else}
					<p class="empty-hint">
						Entries need location data to appear on the map.
					</p>
				{/if}
			</div>
		{/if}
	{:else}
		{#if listData && listData.entries.length > 0}
			<div class="entries-list">
				{#each listData.entries as entry (entry.uuid)}
					<EntryCard {entry} />
				{/each}
			</div>

			{#if totalPages > 1}
				<div class="pagination">
					<button class="page-button" onclick={prevPage} disabled={currentPage <= 1}>
						&larr; Previous
					</button>
					<span class="page-info">Page {currentPage} of {totalPages}</span>
					<button
						class="page-button"
						onclick={nextPage}
						disabled={currentPage >= totalPages}
					>
						Next &rarr;
					</button>
				</div>
			{/if}
		{:else}
			<div class="empty-state">
				<p class="empty-text">No entries found.</p>
				{#if query || tag || place || dateFrom || dateTo}
					<p class="empty-hint">Try adjusting your filters.</p>
				{:else}
					<p class="empty-hint">
						<a href="/import">Import your journal</a> to get started.
					</p>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<style>
	.search-page {
		max-width: 800px;
	}

	.page-title {
		font-size: 28px;
		font-weight: 700;
		margin-bottom: 24px;
	}

	.controls-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 20px;
	}

	.tab-toggle {
		display: flex;
		background: var(--color-bg);
		border-radius: var(--radius-sm);
		padding: 3px;
		gap: 2px;
	}

	.tab-button {
		padding: 7px 18px;
		border: none;
		border-radius: 4px;
		background: transparent;
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text-secondary);
		transition: all 0.15s ease;
	}

	.tab-button:hover {
		color: var(--color-text);
	}

	.tab-button.active {
		background: var(--color-surface);
		color: var(--color-text);
		box-shadow: var(--shadow-sm);
	}

	.result-count {
		font-size: 14px;
		color: var(--color-text-tertiary);
	}

	.timeline {
		display: flex;
		flex-direction: column;
		gap: 32px;
	}

	.timeline-group {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.month-header {
		font-family: var(--font-serif);
		font-size: 20px;
		font-weight: 400;
		color: var(--color-text);
		padding-bottom: 8px;
		border-bottom: 1px solid var(--color-border);
	}

	.month-count {
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--color-text-tertiary);
		font-weight: 400;
	}

	.entries-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.load-more {
		display: flex;
		justify-content: center;
		padding: 8px 0;
	}

	.load-more-button {
		padding: 10px 28px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
		color: var(--color-text-secondary);
		transition: all 0.15s ease;
	}

	.load-more-button:hover {
		border-color: var(--color-accent);
		color: var(--color-accent);
	}

	.loading {
		display: flex;
		justify-content: center;
		padding: 60px 0;
	}

	.loading-text {
		color: var(--color-text-tertiary);
		font-size: 15px;
	}

	.pagination {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 16px;
		padding: 16px 0;
	}

	.page-button {
		padding: 8px 20px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
		color: var(--color-text-secondary);
		transition: all 0.15s ease;
	}

	.page-button:hover:not(:disabled) {
		border-color: var(--color-accent);
		color: var(--color-accent);
	}

	.page-button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.page-info {
		font-size: 14px;
		color: var(--color-text-tertiary);
	}

	.error-state {
		text-align: center;
		padding: 60px 0;
	}

	.error-message {
		color: var(--color-danger);
		font-size: 14px;
		margin-bottom: 16px;
	}

	.retry-button {
		padding: 8px 20px;
		background: var(--color-accent);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
	}

	.empty-state {
		text-align: center;
		padding: 60px 0;
	}

	.empty-text {
		font-size: 16px;
		color: var(--color-text-secondary);
		margin-bottom: 8px;
	}

	.empty-hint {
		font-size: 14px;
		color: var(--color-text-tertiary);
	}
</style>
