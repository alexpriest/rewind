<script lang="ts">
	import { onMount } from 'svelte';
	import { getGraph, getNodeEntries } from '$lib/api';
	import type { GraphNode, GraphEdge, GraphData, Entry } from '$lib/types';
	import ForceGraph from '$lib/components/ForceGraph.svelte';
	import GraphControls from '$lib/components/GraphControls.svelte';
	import NodePanel from '$lib/components/NodePanel.svelte';

	let graphData: GraphData | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

	let filterTypes = $state({ person: true, place: true, topic: true });
	let dateFrom = $state('');
	let dateTo = $state('');
	let minWeight = $state(1);

	let selectedNode: GraphNode | null = $state(null);
	let nodeEntries: Entry[] = $state([]);
	let nodeEntriesLoading = $state(false);

	const maxWeight = $derived.by(() => {
		if (!graphData) return 1;
		return Math.max(1, ...graphData.edges.map((e: GraphEdge) => e.weight));
	});

	const filteredNodes = $derived.by(() => {
		if (!graphData) return [];
		return graphData.nodes.filter((n) => {
			if (!filterTypes[n.node_type]) return false;
			if (dateFrom && n.last_date && n.last_date < dateFrom) return false;
			if (dateTo && n.first_date && n.first_date > dateTo) return false;
			return true;
		});
	});

	const filteredEdges = $derived.by(() => {
		if (!graphData) return [];
		const nodeKeys = new Set(filteredNodes.map((n) => `${n.node_type}:${n.node_id}`));
		return graphData.edges.filter((e) => {
			if (e.weight < minWeight) return false;
			const sourceKey = `${e.source_type}:${e.source_id}`;
			const targetKey = `${e.target_type}:${e.target_id}`;
			if (!nodeKeys.has(sourceKey) || !nodeKeys.has(targetKey)) return false;
			if (dateFrom && e.last_date && e.last_date < dateFrom) return false;
			if (dateTo && e.first_date && e.first_date > dateTo) return false;
			return true;
		});
	});

	function handleControlChange(params: {
		types: { person: boolean; place: boolean; topic: boolean };
		dateFrom: string;
		dateTo: string;
		minWeight: number;
	}) {
		filterTypes = params.types;
		dateFrom = params.dateFrom;
		dateTo = params.dateTo;
		minWeight = params.minWeight;
	}

	async function handleNodeClick(node: GraphNode) {
		selectedNode = node;
		nodeEntries = [];
		nodeEntriesLoading = true;
		try {
			nodeEntries = await getNodeEntries(node.node_type, node.node_id);
		} catch {
			nodeEntries = [];
		} finally {
			nodeEntriesLoading = false;
		}
	}

	function closePanel() {
		selectedNode = null;
		nodeEntries = [];
	}

	onMount(async () => {
		try {
			graphData = await getGraph();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load graph';
		} finally {
			loading = false;
		}
	});
</script>

<div class="explore-page">
	<h1 class="page-title">Explore</h1>

	{#if loading}
		<div class="loading-state">
			<p>Loading graph...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p>Could not load graph data.</p>
			<p class="error-detail">{error}</p>
		</div>
	{:else if !graphData || graphData.nodes.length === 0}
		<div class="empty-state">
			<p class="empty-text">No graph data yet</p>
			<p class="empty-hint">
				Import your journal to see connections between people, places, and topics.
			</p>
			<a href="/import" class="import-link">Go to Import</a>
		</div>
	{:else}
		<GraphControls
			types={filterTypes}
			dateRange={[dateFrom, dateTo]}
			{minWeight}
			{maxWeight}
			onchange={handleControlChange}
		/>

		<div class="graph-layout">
			<div class="graph-area">
				{#key `${filteredNodes.length}-${filteredEdges.length}-${minWeight}-${dateFrom}-${dateTo}`}
					<ForceGraph
						nodes={filteredNodes}
						edges={filteredEdges}
						onnodeclick={handleNodeClick}
					/>
				{/key}
			</div>

			{#if selectedNode}
				<NodePanel
					node={selectedNode}
					entries={nodeEntries}
					loading={nodeEntriesLoading}
					onclose={closePanel}
				/>
			{/if}
		</div>
	{/if}
</div>

<style>
	.explore-page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 64px);
	}

	.page-title {
		font-size: 28px;
		font-weight: 700;
		margin-bottom: 16px;
		flex-shrink: 0;
	}

	.graph-layout {
		display: flex;
		gap: 16px;
		flex: 1;
		min-height: 0;
		margin-top: 16px;
	}

	.graph-area {
		flex: 1;
		min-width: 0;
	}

	.loading-state,
	.error-state,
	.empty-state {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 48px 40px;
		text-align: center;
	}

	.loading-state p,
	.error-state p {
		font-size: 15px;
		color: var(--color-text-secondary);
	}

	.error-detail {
		font-size: 13px;
		color: var(--color-text-tertiary);
		margin-top: 4px;
	}

	.empty-text {
		font-size: 16px;
		color: var(--color-text-secondary);
		margin-bottom: 8px;
	}

	.empty-hint {
		font-size: 14px;
		color: var(--color-text-tertiary);
		line-height: 1.5;
		margin-bottom: 16px;
	}

	.import-link {
		display: inline-block;
		padding: 8px 20px;
		background: var(--color-accent);
		color: white;
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
		transition: background 0.15s ease;
	}

	.import-link:hover {
		background: var(--color-accent-dark);
		color: white;
	}
</style>
