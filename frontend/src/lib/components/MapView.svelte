<script lang="ts">
	import type { MapPoint } from '$lib/types';
	import { onMount } from 'svelte';

	let {
		points,
		onpointclick
	}: {
		points: MapPoint[];
		onpointclick?: (uuid: string) => void;
	} = $props();

	let mapContainer: HTMLDivElement | undefined = $state();
	// Using any types since L is dynamically imported
	let mapInstance: any = $state(null);
	let markerGroup: any = $state(null);
	let leaflet: any = $state(null);

	onMount(async () => {
		if (!mapContainer) return;

		// Dynamic imports to avoid SSR issues
		const L = await import('leaflet');
		await import('leaflet/dist/leaflet.css');

		// markercluster expects L as a global
		(window as any).L = L;
		await import('leaflet.markercluster');
		await import('leaflet.markercluster/dist/MarkerCluster.css');
		await import('leaflet.markercluster/dist/MarkerCluster.Default.css');

		leaflet = L;

		// Fix Leaflet default icon paths
		delete (L.Icon.Default.prototype as any)._getIconUrl;
		L.Icon.Default.mergeOptions({
			iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
			iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
			shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
		});

		// Create map
		const map = L.map(mapContainer).setView([39.8, -98.5], 4);

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; OpenStreetMap contributors',
			maxZoom: 19
		}).addTo(map);

		mapInstance = map;

		// Create marker cluster group
		// @ts-ignore — markercluster extends L
		markerGroup = L.markerClusterGroup({
			maxClusterRadius: 50,
			spiderfyOnMaxZoom: true,
			showCoverageOnHover: false,
			zoomToBoundsOnClick: true
		});

		map.addLayer(markerGroup);

		// Add initial markers
		updateMarkers(points);

		return () => {
			map.remove();
		};
	});

	function updateMarkers(pts: MapPoint[]) {
		if (!markerGroup || !mapInstance || !leaflet) return;

		const L = leaflet;

		markerGroup.clearLayers();

		if (pts.length === 0) return;

		const markers: any[] = [];

		for (const pt of pts) {
			const marker = L.marker([pt.latitude, pt.longitude]);

			// Build popup content
			const date = new Date(pt.creation_date).toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			});

			let popupHtml = `<div style="max-width: 240px; font-family: Inter, -apple-system, sans-serif;">`;
			popupHtml += `<div style="font-size: 12px; color: #9b9590; margin-bottom: 4px;">${date}</div>`;

			if (pt.place_name) {
				popupHtml += `<div style="font-size: 12px; color: #4a9e7a; margin-bottom: 6px;">${pt.place_name}</div>`;
			}

			if (pt.snippet) {
				const text = pt.snippet.length > 120 ? pt.snippet.slice(0, 120) + '...' : pt.snippet;
				popupHtml += `<div style="font-size: 13px; color: #2d2a26; line-height: 1.4;">${text}</div>`;
			}

			if (pt.photo_id) {
				popupHtml += `<div style="margin-top: 6px;"><img src="/api/photos/${pt.photo_id}/thumbnail" style="width: 100%; max-height: 120px; object-fit: cover; border-radius: 4px;" /></div>`;
			}

			popupHtml += `</div>`;

			marker.bindPopup(popupHtml);

			if (onpointclick) {
				marker.on('click', () => onpointclick!(pt.uuid));
			}

			markers.push(marker);
		}

		markerGroup.addLayers(markers);

		// Fit bounds to show all markers
		if (markers.length > 0) {
			const bounds = L.latLngBounds(pts.map((p: MapPoint) => [p.latitude, p.longitude]));
			mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
		}
	}

	// React to points changes
	$effect(() => {
		if (mapInstance && markerGroup && leaflet) {
			updateMarkers(points);
		}
	});
</script>

<div class="map-container" bind:this={mapContainer}></div>

<style>
	.map-container {
		width: 100%;
		height: 500px;
		border-radius: var(--radius-md);
		border: 1px solid var(--color-border);
		overflow: hidden;
	}

	.map-container :global(.leaflet-container) {
		width: 100%;
		height: 100%;
		font-family: var(--font-sans);
	}
</style>
