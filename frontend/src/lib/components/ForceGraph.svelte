<script lang="ts">
	import type { GraphNode, GraphEdge } from '$lib/types';
	import * as d3Force from 'd3-force';
	import * as d3Selection from 'd3-selection';
	import * as d3Zoom from 'd3-zoom';

	let {
		nodes,
		edges,
		onnodeclick
	}: {
		nodes: GraphNode[];
		edges: GraphEdge[];
		onnodeclick: (node: GraphNode) => void;
	} = $props();

	let container: HTMLDivElement | undefined = $state();

	const NODE_COLORS: Record<string, string> = {
		person: '#7c6bc4',
		place: '#4a9e7a',
		topic: '#c49a3c'
	};

	function nodeKey(n: GraphNode): string {
		return `${n.node_type}:${n.node_id}`;
	}

	function nodeRadius(n: GraphNode): number {
		return Math.min(Math.max(Math.sqrt(n.entry_count) * 3 + 4, 4), 30);
	}

	$effect(() => {
		if (!container) return;

		const width = container.clientWidth;
		const height = container.clientHeight;

		// Build D3-compatible data structures
		interface SimNode extends d3Force.SimulationNodeDatum {
			key: string;
			data: GraphNode;
		}

		interface SimLink extends d3Force.SimulationLinkDatum<SimNode> {
			data: GraphEdge;
		}

		const nodeMap = new Map<string, SimNode>();
		const simNodes: SimNode[] = nodes.map((n) => {
			const sn: SimNode = { key: nodeKey(n), data: n };
			nodeMap.set(sn.key, sn);
			return sn;
		});

		const simLinks: SimLink[] = edges
			.map((e) => {
				const sourceKey = `${e.source_type}:${e.source_id}`;
				const targetKey = `${e.target_type}:${e.target_id}`;
				const source = nodeMap.get(sourceKey);
				const target = nodeMap.get(targetKey);
				if (!source || !target) return null;
				return { source, target, data: e } as SimLink;
			})
			.filter((l): l is SimLink => l !== null);

		const maxWeight = Math.max(1, ...simLinks.map((l) => l.data.weight));

		// Create SVG
		const svg = d3Selection
			.select(container)
			.append('svg')
			.attr('width', '100%')
			.attr('height', '100%')
			.attr('viewBox', `0 0 ${width} ${height}`)
			.style('cursor', 'grab');

		const g = svg.append('g');

		// Zoom
		const zoomBehavior = d3Zoom
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.2, 5])
			.on('zoom', (event: d3Zoom.D3ZoomEvent<SVGSVGElement, unknown>) => {
				g.attr('transform', event.transform.toString());
			});

		svg.call(zoomBehavior);

		// Edges
		const linkGroup = g
			.append('g')
			.attr('class', 'links')
			.selectAll('line')
			.data(simLinks)
			.enter()
			.append('line')
			.attr('stroke', '#c8c2ba')
			.attr('stroke-width', 1)
			.attr('stroke-opacity', (d: SimLink) => {
				const normalized = d.data.weight / maxWeight;
				return 0.15 + normalized * 0.45;
			});

		// Nodes
		const nodeGroup = g
			.append('g')
			.attr('class', 'nodes')
			.selectAll('g')
			.data(simNodes)
			.enter()
			.append('g')
			.style('cursor', 'pointer');

		nodeGroup
			.append('circle')
			.attr('r', (d: SimNode) => nodeRadius(d.data))
			.attr('fill', (d: SimNode) => NODE_COLORS[d.data.node_type] || '#999')
			.attr('stroke', '#fff')
			.attr('stroke-width', 1.5)
			.attr('opacity', 0.9);

		// Labels
		nodeGroup
			.append('text')
			.text((d: SimNode) => d.data.label)
			.attr('dx', (d: SimNode) => nodeRadius(d.data) + 4)
			.attr('dy', '0.35em')
			.attr('font-size', '11px')
			.attr('font-family', 'Inter, -apple-system, sans-serif')
			.attr('fill', '#2d2a26')
			.attr('pointer-events', 'none')
			.attr('opacity', (d: SimNode) => (d.data.entry_count > 5 ? 0.85 : 0));

		// Hover interactions
		nodeGroup
			.on('mouseenter', function (_event: MouseEvent, d: SimNode) {
				const connectedKeys = new Set<string>();
				connectedKeys.add(d.key);
				simLinks.forEach((l) => {
					const src = l.source as SimNode;
					const tgt = l.target as SimNode;
					if (src.key === d.key) connectedKeys.add(tgt.key);
					if (tgt.key === d.key) connectedKeys.add(src.key);
				});

				// Dim unconnected nodes
				nodeGroup.select('circle').attr('opacity', (n: SimNode) =>
					connectedKeys.has(n.key) ? 1 : 0.15
				);

				// Highlight connected edges
				linkGroup.attr('stroke-opacity', (l: SimLink) => {
					const src = l.source as SimNode;
					const tgt = l.target as SimNode;
					if (src.key === d.key || tgt.key === d.key) return 0.7;
					return 0.05;
				});

				// Show label for hovered node
				d3Selection.select(this).select('text').attr('opacity', 1);
			})
			.on('mouseleave', function () {
				// Restore all opacities
				nodeGroup.select('circle').attr('opacity', 0.9);
				linkGroup.attr('stroke-opacity', (d: SimLink) => {
					const normalized = d.data.weight / maxWeight;
					return 0.15 + normalized * 0.45;
				});

				// Restore label visibility
				nodeGroup.select('text').attr('opacity', (d: SimNode) =>
					d.data.entry_count > 5 ? 0.85 : 0
				);
			});

		// Click
		nodeGroup.on('click', (_event: MouseEvent, d: SimNode) => {
			onnodeclick(d.data);
		});

		// Drag via pointer events (d3-drag not installed)
		let dragSubject: SimNode | null = null;
		let dragStartPos = { x: 0, y: 0 };

		nodeGroup
			.on('pointerdown', function (event: PointerEvent, d: SimNode) {
				event.stopPropagation();
				dragSubject = d;
				dragStartPos = { x: event.clientX, y: event.clientY };
				simulation.alphaTarget(0.3).restart();
				d.fx = d.x;
				d.fy = d.y;
				(this as SVGGElement).setPointerCapture(event.pointerId);
			})
			.on('pointermove', function (event: PointerEvent) {
				if (!dragSubject) return;
				// Get current zoom transform
				const transform = d3Zoom.zoomTransform(svg.node()!);
				const dx = (event.clientX - dragStartPos.x) / transform.k;
				const dy = (event.clientY - dragStartPos.y) / transform.k;
				dragSubject.fx = (dragSubject.fx ?? dragSubject.x ?? 0) + dx;
				dragSubject.fy = (dragSubject.fy ?? dragSubject.y ?? 0) + dy;
				dragStartPos = { x: event.clientX, y: event.clientY };
			})
			.on('pointerup', function (event: PointerEvent) {
				if (!dragSubject) return;
				(this as SVGGElement).releasePointerCapture(event.pointerId);
				simulation.alphaTarget(0);
				dragSubject.fx = null;
				dragSubject.fy = null;
				dragSubject = null;
			});

		// Force simulation
		const simulation = d3Force
			.forceSimulation<SimNode>(simNodes)
			.force(
				'link',
				d3Force
					.forceLink<SimNode, SimLink>(simLinks)
					.id((d) => d.key)
					.distance((d) => Math.max(40, 150 / (d.data.weight || 1)))
			)
			.force('charge', d3Force.forceManyBody<SimNode>().strength(-150))
			.force('center', d3Force.forceCenter(width / 2, height / 2))
			.force(
				'collide',
				d3Force.forceCollide<SimNode>().radius((d) => nodeRadius(d.data) + 2)
			)
			.on('tick', () => {
				linkGroup
					.attr('x1', (d: SimLink) => (d.source as SimNode).x ?? 0)
					.attr('y1', (d: SimLink) => (d.source as SimNode).y ?? 0)
					.attr('x2', (d: SimLink) => (d.target as SimNode).x ?? 0)
					.attr('y2', (d: SimLink) => (d.target as SimNode).y ?? 0);

				nodeGroup.attr('transform', (d: SimNode) => `translate(${d.x ?? 0},${d.y ?? 0})`);
			});

		return () => {
			simulation.stop();
			svg.remove();
		};
	});
</script>

<div class="graph-container" bind:this={container}></div>

<style>
	.graph-container {
		width: 100%;
		height: 100%;
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
	}
</style>
