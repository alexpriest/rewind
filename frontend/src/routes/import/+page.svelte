<script lang="ts">
	import { uploadJournal, getImportStatus } from '$lib/api';
	import type { ImportStatus } from '$lib/types';

	let dragOver = $state(false);
	let importing = $state(false);
	let status: ImportStatus | null = $state(null);
	let error: string | null = $state(null);
	let pollTimer: ReturnType<typeof setInterval> | null = $state(null);

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file) startImport(file);
	}

	function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) startImport(file);
	}

	async function startImport(file: File) {
		if (!file.name.endsWith('.zip')) {
			error = 'Please upload a .zip file exported from Day One.';
			return;
		}

		error = null;
		importing = true;

		try {
			status = await uploadJournal(file);
			pollTimer = setInterval(pollStatus, 1000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Upload failed';
			importing = false;
		}
	}

	async function pollStatus() {
		if (!status) return;
		try {
			status = await getImportStatus(status.id);
			if (status.status === 'done' || status.status === 'error') {
				if (pollTimer) clearInterval(pollTimer);
				pollTimer = null;
				if (status.status === 'error') {
					error = status.message;
				}
			}
		} catch (e) {
			if (pollTimer) clearInterval(pollTimer);
			pollTimer = null;
			error = e instanceof Error ? e.message : 'Failed to check import status';
		}
	}

	const progressPercent = $derived(status ? Math.round(status.progress) : 0);
	const isDone = $derived(status?.status === 'done');
	const isError = $derived(status?.status === 'error');
</script>

<div class="import-page">
	<h1 class="page-title">Import Journal</h1>
	<p class="page-subtitle">Upload your Day One journal export (.zip file)</p>

	{#if !importing}
		<div
			class="drop-zone"
			class:drag-over={dragOver}
			role="button"
			tabindex="0"
			ondragover={handleDragOver}
			ondragleave={handleDragLeave}
			ondrop={handleDrop}
			onkeydown={(e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					document.getElementById('file-input')?.click();
				}
			}}
		>
			<div class="drop-content">
				<span class="drop-icon">{'\u2191'}</span>
				<p class="drop-text">Drag and drop your journal export here</p>
				<p class="drop-hint">or</p>
				<label class="file-button">
					Choose File
					<input
						id="file-input"
						type="file"
						accept=".zip"
						onchange={handleFileInput}
						hidden
					/>
				</label>
			</div>
		</div>

		{#if error}
			<p class="error-message">{error}</p>
		{/if}

		<div class="instructions">
			<h3>How to export from Day One</h3>
			<ol>
				<li>Open Day One on your Mac</li>
				<li>Go to File &rarr; Export &rarr; JSON (.zip)</li>
				<li>Save the file and upload it here</li>
			</ol>
		</div>
	{:else}
		<div class="progress-section">
			{#if isDone}
				<div class="done-card">
					<span class="done-icon">{'\u2713'}</span>
					<h2 class="done-title">Import Complete</h2>
					<div class="done-stats">
						{#if status?.entry_count}
							<div class="done-stat">
								<span class="done-stat-number">{status.entry_count.toLocaleString()}</span>
								<span class="done-stat-label">entries</span>
							</div>
						{/if}
						{#if status?.tag_count}
							<div class="done-stat">
								<span class="done-stat-number">{status.tag_count}</span>
								<span class="done-stat-label">tags</span>
							</div>
						{/if}
						{#if status?.photo_count}
							<div class="done-stat">
								<span class="done-stat-number">{status.photo_count.toLocaleString()}</span>
								<span class="done-stat-label">photos</span>
							</div>
						{/if}
					</div>
					<a href="/search" class="cta-button">Explore Your Journal</a>
				</div>
			{:else if isError}
				<div class="error-card">
					<h2>Import Failed</h2>
					<p class="error-message">{status?.message ?? 'Unknown error'}</p>
					<button class="retry-button" onclick={() => { importing = false; status = null; error = null; }}>
						Try Again
					</button>
				</div>
			{:else}
				<div class="progress-card">
					<h2 class="progress-title">Importing...</h2>
					<p class="progress-status">{status?.message ?? 'Starting...'}</p>
					<div class="progress-bar-track">
						<div class="progress-bar-fill" style="width: {progressPercent}%"></div>
					</div>
					<p class="progress-percent">{progressPercent}%</p>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.import-page {
		max-width: 600px;
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

	.drop-zone {
		border: 2px dashed var(--color-border);
		border-radius: var(--radius-lg);
		padding: 60px 40px;
		text-align: center;
		cursor: pointer;
		transition: all 0.2s ease;
		background: var(--color-surface);
	}

	.drop-zone:hover,
	.drop-zone.drag-over {
		border-color: var(--color-accent);
		background: var(--color-accent-light);
	}

	.drop-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}

	.drop-icon {
		font-size: 36px;
		color: var(--color-text-tertiary);
		margin-bottom: 8px;
	}

	.drop-text {
		font-size: 16px;
		color: var(--color-text-secondary);
		font-weight: 500;
	}

	.drop-hint {
		font-size: 13px;
		color: var(--color-text-tertiary);
	}

	.file-button {
		display: inline-block;
		padding: 10px 24px;
		background: var(--color-accent);
		color: white;
		font-size: 14px;
		font-weight: 600;
		border-radius: var(--radius-sm);
		cursor: pointer;
		transition: background 0.15s ease;
	}

	.file-button:hover {
		background: var(--color-accent-dark);
	}

	.error-message {
		color: var(--color-danger);
		font-size: 14px;
		margin-top: 16px;
	}

	.instructions {
		margin-top: 40px;
		padding: 24px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.instructions h3 {
		font-size: 15px;
		font-weight: 600;
		margin-bottom: 12px;
	}

	.instructions ol {
		padding-left: 20px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.instructions li {
		font-size: 14px;
		color: var(--color-text-secondary);
		line-height: 1.5;
	}

	.progress-section {
		margin-top: 24px;
	}

	.progress-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 40px;
		text-align: center;
	}

	.progress-title {
		font-size: 20px;
		font-weight: 600;
		margin-bottom: 8px;
	}

	.progress-status {
		color: var(--color-text-secondary);
		font-size: 14px;
		margin-bottom: 24px;
	}

	.progress-bar-track {
		height: 8px;
		background: var(--color-border);
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 12px;
	}

	.progress-bar-fill {
		height: 100%;
		background: var(--color-accent);
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.progress-percent {
		font-size: 14px;
		color: var(--color-text-tertiary);
		font-weight: 500;
	}

	.done-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 48px 40px;
		text-align: center;
	}

	.done-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 56px;
		height: 56px;
		border-radius: 50%;
		background: var(--color-success);
		color: white;
		font-size: 28px;
		margin-bottom: 16px;
	}

	.done-title {
		font-size: 22px;
		font-weight: 600;
		margin-bottom: 24px;
	}

	.done-stats {
		display: flex;
		justify-content: center;
		gap: 40px;
		margin-bottom: 32px;
	}

	.done-stat {
		text-align: center;
	}

	.done-stat-number {
		display: block;
		font-size: 28px;
		font-weight: 700;
		color: var(--color-accent);
	}

	.done-stat-label {
		font-size: 13px;
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
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
	}

	.cta-button:hover {
		background: var(--color-accent-dark);
		color: white;
	}

	.error-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 40px;
		text-align: center;
	}

	.error-card h2 {
		font-size: 20px;
		font-weight: 600;
		margin-bottom: 8px;
	}

	.retry-button {
		margin-top: 20px;
		padding: 10px 24px;
		background: var(--color-accent);
		color: white;
		border: none;
		font-size: 14px;
		font-weight: 600;
		border-radius: var(--radius-sm);
		transition: background 0.15s ease;
	}

	.retry-button:hover {
		background: var(--color-accent-dark);
	}
</style>
