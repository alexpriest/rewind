<script lang="ts">
	import type { Photo } from '$lib/types';

	let {
		photos,
		startIndex = 0,
		onclose
	}: {
		photos: Photo[];
		startIndex?: number;
		onclose: () => void;
	} = $props();

	let currentIndex = $state(startIndex);
	let imageLoaded = $state(false);

	const currentPhoto = $derived(photos[currentIndex]);

	function prev() {
		if (currentIndex > 0) {
			imageLoaded = false;
			currentIndex--;
		}
	}

	function next() {
		if (currentIndex < photos.length - 1) {
			imageLoaded = false;
			currentIndex++;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
		else if (e.key === 'ArrowLeft') prev();
		else if (e.key === 'ArrowRight') next();
	}

	function handleOverlayClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onclose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="lightbox-overlay" onclick={handleOverlayClick} onkeydown={handleKeydown} role="dialog" tabindex="-1">
	<button class="lightbox-close" onclick={onclose} aria-label="Close">
		&times;
	</button>

	<div class="lightbox-content">
		{#if photos.length > 1 && currentIndex > 0}
			<button class="lightbox-arrow lightbox-prev" onclick={prev} aria-label="Previous photo">
				&#8249;
			</button>
		{/if}

		<div class="lightbox-image-wrapper">
			{#if !imageLoaded}
				<div class="lightbox-loading">Loading...</div>
			{/if}
			<img
				src="/api/photos/{currentPhoto.id}/full"
				alt=""
				class="lightbox-image"
				class:visible={imageLoaded}
				onload={() => (imageLoaded = true)}
			/>
		</div>

		{#if photos.length > 1 && currentIndex < photos.length - 1}
			<button class="lightbox-arrow lightbox-next" onclick={next} aria-label="Next photo">
				&#8250;
			</button>
		{/if}
	</div>

	{#if photos.length > 1}
		<div class="lightbox-counter">
			{currentIndex + 1} / {photos.length}
		</div>
	{/if}
</div>

<style>
	.lightbox-overlay {
		position: fixed;
		inset: 0;
		z-index: 1000;
		background: rgba(0, 0, 0, 0.85);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-direction: column;
	}

	.lightbox-close {
		position: absolute;
		top: 16px;
		right: 20px;
		background: none;
		border: none;
		color: rgba(255, 255, 255, 0.8);
		font-size: 36px;
		line-height: 1;
		padding: 4px 8px;
		transition: color 0.15s ease;
		z-index: 1001;
	}

	.lightbox-close:hover {
		color: #ffffff;
	}

	.lightbox-content {
		display: flex;
		align-items: center;
		gap: 16px;
		max-width: 90vw;
		max-height: 85vh;
	}

	.lightbox-arrow {
		background: none;
		border: none;
		color: rgba(255, 255, 255, 0.7);
		font-size: 48px;
		line-height: 1;
		padding: 8px 12px;
		transition: color 0.15s ease;
		flex-shrink: 0;
	}

	.lightbox-arrow:hover {
		color: #ffffff;
	}

	.lightbox-image-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 200px;
		min-height: 200px;
	}

	.lightbox-loading {
		position: absolute;
		color: rgba(255, 255, 255, 0.5);
		font-size: 14px;
	}

	.lightbox-image {
		max-width: 85vw;
		max-height: 85vh;
		object-fit: contain;
		border-radius: var(--radius-sm);
		opacity: 0;
		transition: opacity 0.2s ease;
	}

	.lightbox-image.visible {
		opacity: 1;
	}

	.lightbox-counter {
		position: absolute;
		bottom: 20px;
		left: 50%;
		transform: translateX(-50%);
		color: rgba(255, 255, 255, 0.7);
		font-size: 14px;
		font-weight: 500;
	}
</style>
