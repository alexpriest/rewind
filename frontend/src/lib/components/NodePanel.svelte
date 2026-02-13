<script lang="ts">
	import type { GraphNode, Entry } from '$lib/types';

	let {
		node,
		entries,
		loading,
		onclose
	}: {
		node: GraphNode;
		entries: Entry[];
		loading: boolean;
		onclose: () => void;
	} = $props();

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function truncate(text: string, max: number): string {
		if (text.length <= max) return text;
		return text.slice(0, max).trimEnd() + '...';
	}

	function displayText(entry: Entry): string {
		if (entry.snippet) return truncate(entry.snippet, 100);
		if (entry.text) return truncate(entry.text, 100);
		return '';
	}

	const typeLabel: Record<string, string> = {
		person: 'Person',
		place: 'Place',
		topic: 'Topic'
	};

	const typeColor: Record<string, string> = {
		person: '#7c6bc4',
		place: '#4a9e7a',
		topic: '#c49a3c'
	};
</script>

<aside class="node-panel">
	<header class="panel-header">
		<div class="panel-title-row">
			<h3 class="panel-title">{node.label}</h3>
			<button class="close-btn" onclick={onclose}>&times;</button>
		</div>
		<div class="panel-meta">
			<span class="type-badge" style="background: {typeColor[node.node_type] || '#999'}">
				{typeLabel[node.node_type] || node.node_type}
			</span>
			<span class="entry-count">{node.entry_count} {node.entry_count === 1 ? 'entry' : 'entries'}</span>
		</div>
	</header>

	<div class="panel-body">
		{#if loading}
			<div class="loading">Loading entries...</div>
		{:else if entries.length === 0}
			<div class="empty">No entries found</div>
		{:else}
			<ul class="entry-list">
				{#each entries as entry}
					<li>
						<a class="entry-item" href="/search?tag={encodeURIComponent(node.label)}">
							<time class="item-date">{formatDate(entry.creation_date)}</time>
							{#if displayText(entry)}
								<p class="item-text">{displayText(entry)}</p>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
</aside>

<style>
	.node-panel {
		width: 300px;
		min-width: 300px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		animation: slideIn 0.2s ease;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(12px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.panel-header {
		padding: 16px 16px 12px;
		border-bottom: 1px solid var(--color-border);
	}

	.panel-title-row {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 8px;
	}

	.panel-title {
		font-size: 16px;
		font-weight: 700;
		color: var(--color-text);
		line-height: 1.3;
		word-break: break-word;
	}

	.close-btn {
		background: none;
		border: none;
		font-size: 22px;
		line-height: 1;
		color: var(--color-text-tertiary);
		padding: 0 4px;
		flex-shrink: 0;
		transition: color 0.15s ease;
	}

	.close-btn:hover {
		color: var(--color-text);
	}

	.panel-meta {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.type-badge {
		font-size: 11px;
		font-weight: 600;
		color: white;
		padding: 2px 8px;
		border-radius: 100px;
		text-transform: uppercase;
		letter-spacing: 0.3px;
	}

	.entry-count {
		font-size: 13px;
		color: var(--color-text-tertiary);
	}

	.panel-body {
		flex: 1;
		overflow-y: auto;
		padding: 8px 0;
	}

	.loading,
	.empty {
		padding: 24px 16px;
		text-align: center;
		font-size: 14px;
		color: var(--color-text-tertiary);
	}

	.entry-list {
		list-style: none;
	}

	.entry-item {
		display: block;
		padding: 10px 16px;
		color: inherit;
		transition: background 0.1s ease;
	}

	.entry-item:hover {
		background: var(--color-bg);
		color: inherit;
	}

	.item-date {
		font-family: var(--font-serif);
		font-size: 12px;
		color: var(--color-text-secondary);
		display: block;
		margin-bottom: 3px;
	}

	.item-text {
		font-size: 13px;
		line-height: 1.5;
		color: var(--color-text);
	}
</style>
