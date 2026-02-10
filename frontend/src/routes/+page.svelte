<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntries, getTags } from '$lib/api';
	import type { EntryListResponse, Tag } from '$lib/types';
	import EntryCard from '$lib/components/EntryCard.svelte';

	let entryData: EntryListResponse | null = $state(null);
	let tags: Tag[] = $state([]);
	let loading = $state(true);
	let hasData = $state(false);

	onMount(async () => {
		try {
			[entryData, tags] = await Promise.all([getEntries({ page: 1, page_size: 5 }), getTags()]);
			hasData = (entryData?.total ?? 0) > 0;
		} catch {
			hasData = false;
		} finally {
			loading = false;
		}
	});

	const peopleCount = $derived(tags.filter((t) => t.tag_type === 'person').length);
	const topTags = $derived(
		[...tags].sort((a, b) => b.entry_count - a.entry_count).slice(0, 10)
	);
</script>

<div class="home">
	{#if loading}
		<div class="loading">
			<p class="loading-text">Loading...</p>
		</div>
	{:else if hasData && entryData}
		<h1 class="page-title">Your Journal</h1>
		<p class="page-subtitle">A window into your memories</p>

		<div class="stats-grid">
			<div class="stat-card">
				<span class="stat-number">{entryData.total.toLocaleString()}</span>
				<span class="stat-label">Entries</span>
			</div>
			<div class="stat-card">
				<span class="stat-number">{tags.length}</span>
				<span class="stat-label">Tags</span>
			</div>
			<div class="stat-card">
				<span class="stat-number">{peopleCount}</span>
				<span class="stat-label">People</span>
			</div>
		</div>

		{#if topTags.length > 0}
			<section class="section">
				<h2 class="section-title">Top Tags</h2>
				<div class="tag-chips">
					{#each topTags as tag}
						<a href="/search?tag={encodeURIComponent(tag.name)}" class="tag-chip">
							{tag.name}
							<span class="tag-count">{tag.entry_count}</span>
						</a>
					{/each}
				</div>
			</section>
		{/if}

		<section class="section">
			<h2 class="section-title">Recent Entries</h2>
			<div class="entries-list">
				{#each entryData.entries as entry (entry.uuid)}
					<EntryCard {entry} />
				{/each}
			</div>
			<a href="/search" class="view-all">View all entries &rarr;</a>
		</section>
	{:else}
		<div class="welcome">
			<div class="welcome-content">
				<h1 class="welcome-title">Welcome to Rewind</h1>
				<p class="welcome-text">
					Rewind helps you explore and visualize your Day One journal. See your memories through
					new eyes — discover connections between people, places, and moments in your life.
				</p>
				<a href="/import" class="cta-button">Import Your Journal</a>
				<p class="welcome-hint">
					Export your journal from Day One as a JSON zip file, then upload it here.
				</p>
			</div>
		</div>
	{/if}
</div>

<style>
	.home {
		max-width: 800px;
	}

	.loading {
		display: flex;
		justify-content: center;
		padding: 80px 0;
	}

	.loading-text {
		color: var(--color-text-tertiary);
		font-size: 15px;
	}

	.page-title {
		font-size: 28px;
		font-weight: 700;
		margin-bottom: 4px;
	}

	.page-subtitle {
		color: var(--color-text-secondary);
		font-size: 15px;
		margin-bottom: 32px;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px;
		margin-bottom: 40px;
	}

	.stat-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 24px;
		text-align: center;
		box-shadow: var(--shadow-sm);
	}

	.stat-number {
		display: block;
		font-size: 32px;
		font-weight: 700;
		color: var(--color-accent);
		margin-bottom: 4px;
	}

	.stat-label {
		font-size: 13px;
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		font-weight: 500;
	}

	.section {
		margin-bottom: 40px;
	}

	.section-title {
		font-size: 18px;
		font-weight: 600;
		margin-bottom: 16px;
	}

	.tag-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.tag-chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 6px 14px;
		border-radius: 100px;
		background: var(--color-accent-light);
		color: var(--color-accent-dark);
		font-size: 13px;
		font-weight: 500;
		transition: background 0.15s ease;
	}

	.tag-chip:hover {
		background: var(--color-accent);
		color: white;
	}

	.tag-count {
		font-size: 11px;
		opacity: 0.7;
	}

	.entries-list {
		display: flex;
		flex-direction: column;
		gap: 16px;
		margin-bottom: 16px;
	}

	.view-all {
		font-size: 14px;
		font-weight: 500;
	}

	.welcome {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 60vh;
	}

	.welcome-content {
		text-align: center;
		max-width: 480px;
	}

	.welcome-title {
		font-size: 36px;
		font-weight: 700;
		margin-bottom: 16px;
		color: var(--color-text);
	}

	.welcome-text {
		font-size: 16px;
		line-height: 1.6;
		color: var(--color-text-secondary);
		margin-bottom: 32px;
	}

	.cta-button {
		display: inline-block;
		padding: 14px 32px;
		background: var(--color-accent);
		color: white;
		font-size: 16px;
		font-weight: 600;
		border-radius: var(--radius-md);
		transition: background 0.15s ease;
		margin-bottom: 16px;
	}

	.cta-button:hover {
		background: var(--color-accent-dark);
		color: white;
	}

	.welcome-hint {
		font-size: 13px;
		color: var(--color-text-tertiary);
	}
</style>
