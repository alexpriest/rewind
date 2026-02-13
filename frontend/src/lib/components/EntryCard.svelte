<script lang="ts">
	import type { Entry } from '$lib/types';
	import Lightbox from './Lightbox.svelte';

	let { entry }: { entry: Entry } = $props();

	let lightboxOpen = $state(false);
	let lightboxStartIndex = $state(0);

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function displayText(e: Entry): string {
		if (e.snippet) return e.snippet;
		if (e.text) return e.text.slice(0, 200) + (e.text.length > 200 ? '...' : '');
		return '';
	}

	function locationString(e: Entry): string {
		const parts = [e.place_name, e.locality, e.country].filter(Boolean);
		return parts.join(', ');
	}

	function weatherString(e: Entry): string {
		const parts: string[] = [];
		if (e.weather_description) parts.push(e.weather_description);
		if (e.weather_temp_c !== null) parts.push(`${Math.round(e.weather_temp_c)}\u00B0C`);
		return parts.join(' \u00B7 ');
	}

	function openLightbox(index: number) {
		lightboxStartIndex = index;
		lightboxOpen = true;
	}

	const visiblePhotos = $derived(entry.photos.filter((p) => p.has_thumbnail).slice(0, 4));
	const photoCount = $derived(entry.photos.filter((p) => p.has_thumbnail).length);
</script>

<article class="entry-card">
	<header class="entry-header">
		<time class="entry-date">{formatDate(entry.creation_date)}</time>
		{#if entry.starred}
			<span class="star" title="Starred">&#9733;</span>
		{/if}
	</header>

	{#if displayText(entry)}
		<p class="entry-text">{displayText(entry)}</p>
	{/if}

	{#if visiblePhotos.length > 0}
		<div class="entry-photos" class:grid={visiblePhotos.length >= 2}>
			{#each visiblePhotos as photo, i}
				<button class="photo-button" onclick={() => openLightbox(i)}>
					<img
						src="/api/photos/{photo.id}/thumbnail"
						alt=""
						class="photo-thumb"
						loading="lazy"
					/>
				</button>
			{/each}
			{#if photoCount > 4}
				<button class="photo-more-overlay" onclick={() => openLightbox(3)}>
					+{photoCount - 4}
				</button>
			{/if}
		</div>
	{/if}

	<footer class="entry-footer">
		{#if locationString(entry)}
			<span class="entry-meta location">{locationString(entry)}</span>
		{/if}
		{#if weatherString(entry)}
			<span class="entry-meta weather">{weatherString(entry)}</span>
		{/if}
		{#if entry.word_count}
			<span class="entry-meta words">{entry.word_count} words</span>
		{/if}
	</footer>

	{#if entry.tags.length > 0}
		<div class="entry-tags">
			{#each entry.tags as tag}
				<span class="tag-chip">{tag}</span>
			{/each}
		</div>
	{/if}
</article>

{#if lightboxOpen}
	<Lightbox
		photos={entry.photos.filter((p) => p.has_thumbnail)}
		startIndex={lightboxStartIndex}
		onclose={() => (lightboxOpen = false)}
	/>
{/if}

<style>
	.entry-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 24px;
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.15s ease;
	}

	.entry-card:hover {
		box-shadow: var(--shadow-md);
	}

	.entry-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 12px;
	}

	.entry-date {
		font-family: var(--font-serif);
		font-size: 15px;
		color: var(--color-text-secondary);
	}

	.star {
		color: var(--color-starred);
		font-size: 18px;
	}

	.entry-text {
		font-size: 15px;
		line-height: 1.6;
		color: var(--color-text);
		margin-bottom: 16px;
	}

	.entry-photos {
		display: flex;
		gap: 8px;
		margin-bottom: 16px;
		align-items: center;
		position: relative;
	}

	.entry-photos.grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
		max-width: 256px;
	}

	.photo-button {
		background: none;
		border: none;
		padding: 0;
		line-height: 0;
		border-radius: var(--radius-sm);
		overflow: hidden;
		transition: opacity 0.15s ease;
	}

	.photo-button:hover {
		opacity: 0.85;
	}

	.photo-thumb {
		width: 120px;
		height: 120px;
		object-fit: cover;
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		display: block;
	}

	.photo-more-overlay {
		position: absolute;
		bottom: 0;
		right: 0;
		width: 120px;
		height: 120px;
		background: rgba(0, 0, 0, 0.45);
		color: white;
		font-size: 16px;
		font-weight: 600;
		border: none;
		border-radius: var(--radius-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.15s ease;
	}

	.photo-more-overlay:hover {
		background: rgba(0, 0, 0, 0.55);
	}

	.entry-footer {
		display: flex;
		flex-wrap: wrap;
		gap: 16px;
		margin-bottom: 12px;
	}

	.entry-meta {
		font-size: 13px;
		color: var(--color-text-tertiary);
	}

	.entry-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.tag-chip {
		font-size: 12px;
		padding: 3px 10px;
		border-radius: 100px;
		background: var(--color-accent-light);
		color: var(--color-accent-dark);
		font-weight: 500;
	}
</style>
