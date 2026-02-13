<script lang="ts">
	import { onMount } from 'svelte';
	import { getTags, generateReport, getReportStatus } from '$lib/api';
	import type { Tag, ReportStatus } from '$lib/types';

	let personTags = $state<Tag[]>([]);
	let selectedTagId = $state<number | null>(null);
	let dateFrom = $state('');
	let dateTo = $state('');

	let loading = $state(false);
	let reportStatus = $state<ReportStatus | null>(null);
	let pollInterval = $state<ReturnType<typeof setInterval> | null>(null);

	let searchQuery = $state('');

	const filteredTags = $derived(
		personTags.filter(
			(t) =>
				t.name.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);

	const selectedTag = $derived(
		personTags.find((t) => t.id === selectedTagId) ?? null
	);

	onMount(async () => {
		try {
			const allTags = await getTags();
			personTags = allTags
				.filter((t) => t.tag_type === 'person')
				.sort((a, b) => b.entry_count - a.entry_count);
		} catch {
			// silently fail — will show empty
		}

		return () => {
			if (pollInterval) clearInterval(pollInterval);
		};
	});

	async function startGeneration() {
		if (!selectedTagId) return;

		loading = true;
		reportStatus = null;

		try {
			const status = await generateReport({
				person_tag_id: selectedTagId,
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined
			});

			reportStatus = status;

			// Start polling
			pollInterval = setInterval(async () => {
				if (!reportStatus) return;
				try {
					const updated = await getReportStatus(reportStatus.id);
					reportStatus = updated;

					if (updated.status === 'done' || updated.status === 'error') {
						if (pollInterval) {
							clearInterval(pollInterval);
							pollInterval = null;
						}
						loading = false;
					}
				} catch {
					if (pollInterval) {
						clearInterval(pollInterval);
						pollInterval = null;
					}
					loading = false;
				}
			}, 1000);
		} catch (e) {
			reportStatus = {
				id: '',
				status: 'error',
				progress: 0,
				message: e instanceof Error ? e.message : 'Failed to start report',
				person_name: null
			};
			loading = false;
		}
	}

	function downloadReport() {
		if (!reportStatus || reportStatus.status !== 'done') return;
		window.open(`/api/reports/${reportStatus.id}/html`, '_blank');
	}

	function resetReport() {
		reportStatus = null;
		loading = false;
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}
</script>

<div class="reports-page">
	<h1 class="page-title">Reports</h1>
	<p class="page-subtitle">Generate a personalized narrative report about someone in your journal.</p>

	{#if reportStatus && (reportStatus.status === 'generating' || reportStatus.status === 'done' || reportStatus.status === 'error')}
		<div class="report-result">
			{#if reportStatus.status === 'generating'}
				<div class="generating-card">
					<div class="progress-section">
						<div class="progress-bar-container">
							<div class="progress-bar" style="width: {reportStatus.progress * 100}%"></div>
						</div>
						<p class="progress-message">{reportStatus.message}</p>
					</div>
				</div>
			{:else if reportStatus.status === 'done'}
				<div class="done-card">
					<h2 class="done-title">Report Ready</h2>
					<p class="done-subtitle">
						{#if reportStatus.person_name}
							Report for <strong>{reportStatus.person_name}</strong>
						{/if}
					</p>

					<div class="report-preview">
						<iframe
							src="/api/reports/{reportStatus.id}/html"
							title="Report Preview"
						></iframe>
					</div>

					<div class="report-actions">
						<button class="btn-primary" onclick={downloadReport}>
							Open Full Report
						</button>
						<button class="btn-secondary" onclick={resetReport}>
							Generate Another
						</button>
					</div>
				</div>
			{:else if reportStatus.status === 'error'}
				<div class="error-card">
					<p class="error-text">{reportStatus.message}</p>
					<button class="btn-secondary" onclick={resetReport}>Try Again</button>
				</div>
			{/if}
		</div>
	{:else}
		<div class="builder-card">
			<div class="form-group">
				<label class="form-label">Person</label>
				<div class="person-picker">
					<input
						type="text"
						class="search-input"
						placeholder="Search people..."
						bind:value={searchQuery}
					/>
					<div class="person-list">
						{#if filteredTags.length > 0}
							{#each filteredTags as tag (tag.id)}
								<button
									class="person-option"
									class:selected={selectedTagId === tag.id}
									onclick={() => selectedTagId = tag.id}
								>
									<span class="person-name">{tag.name}</span>
									<span class="person-count">{tag.entry_count} entries</span>
								</button>
							{/each}
						{:else if personTags.length === 0}
							<p class="empty-hint">No people found. Import your journal and classify tags first.</p>
						{:else}
							<p class="empty-hint">No matches for "{searchQuery}"</p>
						{/if}
					</div>
				</div>
			</div>

			<div class="form-row">
				<div class="form-group">
					<label class="form-label">From (optional)</label>
					<input type="date" class="date-input" bind:value={dateFrom} />
				</div>
				<div class="form-group">
					<label class="form-label">To (optional)</label>
					<input type="date" class="date-input" bind:value={dateTo} />
				</div>
			</div>

			{#if selectedTag}
				<div class="selection-summary">
					Generating report for <strong>{selectedTag.name}</strong>
					({selectedTag.entry_count} entries)
					{#if dateFrom || dateTo}
						<span class="date-range-note">
							{#if dateFrom && dateTo}
								from {dateFrom} to {dateTo}
							{:else if dateFrom}
								from {dateFrom}
							{:else}
								until {dateTo}
							{/if}
						</span>
					{/if}
				</div>
			{/if}

			<button
				class="btn-primary generate-button"
				onclick={startGeneration}
				disabled={!selectedTagId || loading}
			>
				{#if loading}
					Generating...
				{:else}
					Generate Report
				{/if}
			</button>
		</div>
	{/if}
</div>

<style>
	.reports-page {
		max-width: 800px;
	}

	.page-title {
		font-size: 28px;
		font-weight: 700;
		margin-bottom: 8px;
	}

	.page-subtitle {
		font-size: 15px;
		color: var(--color-text-tertiary);
		margin-bottom: 32px;
	}

	.builder-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 32px;
	}

	.form-group {
		margin-bottom: 20px;
	}

	.form-label {
		display: block;
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text-secondary);
		margin-bottom: 8px;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.person-picker {
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		overflow: hidden;
	}

	.search-input {
		width: 100%;
		padding: 10px 14px;
		border: none;
		border-bottom: 1px solid var(--color-border);
		font-size: 14px;
		background: var(--color-bg);
		outline: none;
	}

	.search-input:focus {
		background: white;
	}

	.person-list {
		max-height: 240px;
		overflow-y: auto;
	}

	.person-option {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		padding: 10px 14px;
		border: none;
		background: transparent;
		font-size: 14px;
		text-align: left;
		transition: background 0.1s;
	}

	.person-option:hover {
		background: var(--color-bg);
	}

	.person-option.selected {
		background: var(--color-accent-light);
	}

	.person-name {
		font-weight: 500;
		color: var(--color-person);
	}

	.person-count {
		font-size: 12px;
		color: var(--color-text-tertiary);
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
	}

	.date-input {
		width: 100%;
		padding: 9px 12px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		background: var(--color-bg);
	}

	.date-input:focus {
		outline: none;
		border-color: var(--color-accent);
	}

	.selection-summary {
		padding: 12px 16px;
		background: var(--color-accent-light);
		border-radius: var(--radius-sm);
		font-size: 14px;
		color: var(--color-accent-dark);
		margin-bottom: 20px;
	}

	.date-range-note {
		color: var(--color-text-tertiary);
	}

	.generate-button {
		width: 100%;
		padding: 12px;
		font-size: 15px;
	}

	.btn-primary {
		padding: 10px 24px;
		background: var(--color-accent);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 600;
		transition: background 0.15s;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-accent-dark);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-secondary {
		padding: 10px 24px;
		background: var(--color-surface);
		color: var(--color-text-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 14px;
		font-weight: 500;
		transition: all 0.15s;
	}

	.btn-secondary:hover {
		border-color: var(--color-accent);
		color: var(--color-accent);
	}

	.report-result {
		max-width: 800px;
	}

	.generating-card, .done-card, .error-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 32px;
	}

	.progress-section {
		text-align: center;
	}

	.progress-bar-container {
		width: 100%;
		height: 6px;
		background: var(--color-bg);
		border-radius: 3px;
		overflow: hidden;
		margin-bottom: 16px;
	}

	.progress-bar {
		height: 100%;
		background: var(--color-accent);
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	.progress-message {
		font-size: 14px;
		color: var(--color-text-secondary);
	}

	.done-title {
		font-size: 20px;
		font-weight: 700;
		margin-bottom: 4px;
	}

	.done-subtitle {
		font-size: 14px;
		color: var(--color-text-secondary);
		margin-bottom: 20px;
	}

	.report-preview {
		margin-bottom: 20px;
	}

	.report-preview iframe {
		width: 100%;
		height: 500px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
	}

	.report-actions {
		display: flex;
		gap: 12px;
	}

	.error-card {
		text-align: center;
	}

	.error-text {
		color: var(--color-danger);
		font-size: 14px;
		margin-bottom: 16px;
	}

	.empty-hint {
		padding: 20px;
		text-align: center;
		font-size: 14px;
		color: var(--color-text-tertiary);
	}
</style>
