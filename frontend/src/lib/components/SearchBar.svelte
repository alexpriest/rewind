<script lang="ts">
	import { onMount } from 'svelte';
	import { getTags } from '$lib/api';
	import type { Tag } from '$lib/types';

	let {
		onfilterchange,
		initialQuery = '',
		initialTag = ''
	}: {
		onfilterchange: (filters: {
			query: string;
			tag: string;
			place: string;
			dateFrom: string;
			dateTo: string;
		}) => void;
		initialQuery?: string;
		initialTag?: string;
	} = $props();

	let query = $state(initialQuery);
	let selectedTag = $state(initialTag);
	let place = $state('');
	let dateFrom = $state('');
	let dateTo = $state('');
	let filtersOpen = $state(false);
	let tags: Tag[] = $state([]);
	let debounceTimer: ReturnType<typeof setTimeout> | undefined;

	function fireChange() {
		onfilterchange({
			query,
			tag: selectedTag,
			place,
			dateFrom,
			dateTo
		});
	}

	function handleQueryInput() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(fireChange, 300);
	}

	function handleQueryKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			clearTimeout(debounceTimer);
			fireChange();
		}
	}

	function selectTag(tagName: string) {
		selectedTag = selectedTag === tagName ? '' : tagName;
		fireChange();
	}

	function handleDateChange() {
		fireChange();
	}

	function handlePlaceInput() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(fireChange, 300);
	}

	const hasActiveFilters = $derived(
		query !== '' || selectedTag !== '' || place !== '' || dateFrom !== '' || dateTo !== ''
	);

	function clearAll() {
		query = '';
		selectedTag = '';
		place = '';
		dateFrom = '';
		dateTo = '';
		fireChange();
	}

	function tagColor(tag: Tag): string {
		if (tag.tag_type === 'person') return 'var(--color-person)';
		if (tag.tag_type === 'topic') return 'var(--color-topic)';
		return 'var(--color-text-tertiary)';
	}

	onMount(async () => {
		try {
			tags = await getTags();
		} catch {
			// Tags fail silently — filter still works without them
		}
	});
</script>

<div class="search-bar">
	<div class="search-row">
		<input
			type="text"
			class="search-input"
			placeholder="Search your journal..."
			bind:value={query}
			oninput={handleQueryInput}
			onkeydown={handleQueryKeydown}
		/>
		<button
			class="filter-toggle"
			class:active={filtersOpen}
			onclick={() => (filtersOpen = !filtersOpen)}
		>
			<span class="filter-icon">&#9776;</span>
			Filters
		</button>
	</div>

	{#if filtersOpen}
		<div class="filter-panel">
			<div class="filter-section">
				<span class="filter-label">Date range</span>
				<div class="date-row">
					<input
						type="date"
						class="date-input"
						bind:value={dateFrom}
						onchange={handleDateChange}
						placeholder="From"
					/>
					<span class="date-separator">&ndash;</span>
					<input
						type="date"
						class="date-input"
						bind:value={dateTo}
						onchange={handleDateChange}
						placeholder="To"
					/>
				</div>
			</div>

			<div class="filter-section">
				<span class="filter-label">Place</span>
				<input
					type="text"
					class="place-input"
					placeholder="Filter by place..."
					bind:value={place}
					oninput={handlePlaceInput}
				/>
			</div>

			{#if tags.length > 0}
				<div class="filter-section">
					<span class="filter-label">Tags</span>
					<div class="tag-chips">
						{#each tags as tag}
							<button
								class="tag-chip"
								class:selected={selectedTag === tag.name}
								style="--tag-color: {tagColor(tag)}"
								onclick={() => selectTag(tag.name)}
							>
								{tag.name}
								<span class="tag-count">{tag.entry_count}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}

			{#if hasActiveFilters}
				<button class="clear-link" onclick={clearAll}>Clear all filters</button>
			{/if}
		</div>
	{/if}
</div>

<style>
	.search-bar {
		margin-bottom: 20px;
	}

	.search-row {
		display: flex;
		gap: 8px;
	}

	.search-input {
		flex: 1;
		padding: 12px 16px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 15px;
		background: var(--color-surface);
		color: var(--color-text);
		outline: none;
		transition: border-color 0.15s ease;
	}

	.search-input:focus {
		border-color: var(--color-accent);
	}

	.search-input::placeholder {
		color: var(--color-text-tertiary);
	}

	.filter-toggle {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 12px 16px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
		color: var(--color-text-secondary);
		transition: all 0.15s ease;
		white-space: nowrap;
	}

	.filter-toggle:hover {
		border-color: var(--color-accent);
		color: var(--color-accent);
	}

	.filter-toggle.active {
		background: var(--color-accent-light);
		border-color: var(--color-accent);
		color: var(--color-accent-dark);
	}

	.filter-icon {
		font-size: 14px;
	}

	.filter-panel {
		margin-top: 12px;
		padding: 20px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.filter-section {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.filter-label {
		font-size: 12px;
		font-weight: 600;
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.date-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.date-input {
		flex: 1;
		padding: 8px 12px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		background: var(--color-surface);
		color: var(--color-text);
		outline: none;
		transition: border-color 0.15s ease;
	}

	.date-input:focus {
		border-color: var(--color-accent);
	}

	.date-separator {
		color: var(--color-text-tertiary);
		font-size: 14px;
	}

	.place-input {
		padding: 8px 12px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		background: var(--color-surface);
		color: var(--color-text);
		outline: none;
		transition: border-color 0.15s ease;
	}

	.place-input:focus {
		border-color: var(--color-accent);
	}

	.place-input::placeholder {
		color: var(--color-text-tertiary);
	}

	.tag-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.tag-chip {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 4px 12px;
		border-radius: 100px;
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		font-size: 13px;
		font-weight: 500;
		color: var(--color-text-secondary);
		transition: all 0.15s ease;
	}

	.tag-chip:hover {
		border-color: var(--tag-color);
		color: var(--tag-color);
	}

	.tag-chip.selected {
		background: var(--tag-color);
		border-color: var(--tag-color);
		color: white;
	}

	.tag-chip.selected .tag-count {
		color: rgba(255, 255, 255, 0.8);
	}

	.tag-count {
		font-size: 11px;
		color: var(--color-text-tertiary);
		font-weight: 400;
	}

	.clear-link {
		background: none;
		border: none;
		color: var(--color-accent);
		font-size: 13px;
		font-weight: 500;
		padding: 0;
		align-self: flex-start;
		transition: color 0.15s ease;
	}

	.clear-link:hover {
		color: var(--color-accent-dark);
	}
</style>
