<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntries } from '$lib/api';
	import type { EntryListResponse } from '$lib/types';
	import EntryCard from '$lib/components/EntryCard.svelte';

	let entryData: EntryListResponse | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);
	let searchQuery = $state('');
	let currentPage = $state(1);
	const pageSize = 20;

	async function loadEntries() {
		loading = true;
		error = null;
		try {
			entryData = await getEntries({
				page: currentPage,
				page_size: pageSize,
				q: searchQuery || undefined
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load entries';
		} finally {
			loading = false;
		}
	}

	function handleSearch(e: SubmitEvent) {
		e.preventDefault();
		currentPage = 1;
		loadEntries();
	}

	function prevPage() {
		if (currentPage > 1) {
			currentPage--;
			loadEntries();
		}
	}

	function nextPage() {
		if (entryData && currentPage * pageSize < entryData.total) {
			currentPage++;
			loadEntries();
		}
	}

	const totalPages = $derived(entryData ? Math.ceil(entryData.total / pageSize) : 0);

	onMount(() => {
		const params = new URLSearchParams(window.location.search);
		const tag = params.get('tag');
		if (tag) {
			searchQuery = tag;
		}
		loadEntries();
	});
</script>

<div class="search-page">
	<h1 class="page-title">Search Entries</h1>

	<form class="search-form" onsubmit={handleSearch}>
		<input
			type="text"
			class="search-input"
			placeholder="Search your journal..."
			bind:value={searchQuery}
		/>
		<button type="submit" class="search-button">Search</button>
	</form>

	{#if loading}
		<div class="loading">
			<p class="loading-text">Loading entries...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button class="retry-button" onclick={loadEntries}>Retry</button>
		</div>
	{:else if entryData && entryData.entries.length > 0}
		<p class="result-count">
			{entryData.total.toLocaleString()} {entryData.total === 1 ? 'entry' : 'entries'} found
		</p>

		<div class="entries-list">
			{#each entryData.entries as entry (entry.uuid)}
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
			{#if searchQuery}
				<p class="empty-hint">Try a different search term.</p>
			{:else}
				<p class="empty-hint">
					<a href="/import">Import your journal</a> to get started.
				</p>
			{/if}
		</div>
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

	.search-form {
		display: flex;
		gap: 8px;
		margin-bottom: 24px;
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

	.search-button {
		padding: 12px 24px;
		background: var(--color-accent);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 600;
		transition: background 0.15s ease;
	}

	.search-button:hover {
		background: var(--color-accent-dark);
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

	.result-count {
		font-size: 14px;
		color: var(--color-text-tertiary);
		margin-bottom: 16px;
	}

	.entries-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
		margin-bottom: 24px;
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
