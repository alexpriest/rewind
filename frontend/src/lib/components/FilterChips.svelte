<script lang="ts">
	let {
		query = '',
		tag = '',
		place = '',
		dateFrom = '',
		dateTo = '',
		onclear,
		onclearall
	}: {
		query?: string;
		tag?: string;
		place?: string;
		dateFrom?: string;
		dateTo?: string;
		onclear: (filter: string) => void;
		onclearall: () => void;
	} = $props();

	const hasFilters = $derived(
		query !== '' || tag !== '' || place !== '' || dateFrom !== '' || dateTo !== ''
	);

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}
</script>

{#if hasFilters}
	<div class="filter-chips">
		{#if query}
			<span class="chip">
				Search: {query}
				<button class="chip-remove" onclick={() => onclear('query')}>&times;</button>
			</span>
		{/if}
		{#if tag}
			<span class="chip chip-tag">
				Tag: {tag}
				<button class="chip-remove" onclick={() => onclear('tag')}>&times;</button>
			</span>
		{/if}
		{#if place}
			<span class="chip chip-place">
				Place: {place}
				<button class="chip-remove" onclick={() => onclear('place')}>&times;</button>
			</span>
		{/if}
		{#if dateFrom}
			<span class="chip">
				From: {formatDate(dateFrom)}
				<button class="chip-remove" onclick={() => onclear('dateFrom')}>&times;</button>
			</span>
		{/if}
		{#if dateTo}
			<span class="chip">
				To: {formatDate(dateTo)}
				<button class="chip-remove" onclick={() => onclear('dateTo')}>&times;</button>
			</span>
		{/if}
		<button class="clear-all" onclick={onclearall}>Clear all</button>
	</div>
{/if}

<style>
	.filter-chips {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 8px;
		margin-bottom: 16px;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 4px 10px;
		border-radius: 100px;
		background: var(--color-accent-light);
		color: var(--color-accent-dark);
		font-size: 13px;
		font-weight: 500;
	}

	.chip-tag {
		background: rgba(124, 107, 196, 0.12);
		color: var(--color-person);
	}

	.chip-place {
		background: rgba(74, 158, 122, 0.12);
		color: var(--color-place);
	}

	.chip-remove {
		background: none;
		border: none;
		color: inherit;
		font-size: 16px;
		line-height: 1;
		padding: 0 2px;
		opacity: 0.6;
		transition: opacity 0.15s ease;
	}

	.chip-remove:hover {
		opacity: 1;
	}

	.clear-all {
		background: none;
		border: none;
		color: var(--color-accent);
		font-size: 13px;
		font-weight: 500;
		padding: 4px 0;
		transition: color 0.15s ease;
	}

	.clear-all:hover {
		color: var(--color-accent-dark);
	}
</style>
