<script lang="ts">
	let {
		types,
		dateRange,
		minWeight,
		maxWeight = 10,
		onchange
	}: {
		types: { person: boolean; place: boolean; topic: boolean };
		dateRange: [string, string];
		minWeight: number;
		maxWeight?: number;
		onchange: (params: {
			types: { person: boolean; place: boolean; topic: boolean };
			dateFrom: string;
			dateTo: string;
			minWeight: number;
		}) => void;
	} = $props();

	let localTypes = $state({ ...types });
	let dateFrom = $state(dateRange[0]);
	let dateTo = $state(dateRange[1]);
	let localMinWeight = $state(minWeight);

	function fireChange() {
		onchange({
			types: { ...localTypes },
			dateFrom,
			dateTo,
			minWeight: localMinWeight
		});
	}

	function toggleType(key: 'person' | 'place' | 'topic') {
		localTypes[key] = !localTypes[key];
		fireChange();
	}

	function handleDateChange() {
		fireChange();
	}

	function handleWeightChange() {
		fireChange();
	}

	function reset() {
		localTypes = { person: true, place: true, topic: true };
		dateFrom = '';
		dateTo = '';
		localMinWeight = 1;
		fireChange();
	}

	const hasNonDefaults = $derived(
		!localTypes.person ||
			!localTypes.place ||
			!localTypes.topic ||
			dateFrom !== '' ||
			dateTo !== '' ||
			localMinWeight > 1
	);
</script>

<div class="graph-controls">
	<div class="control-group">
		<span class="control-label">Show</span>
		<div class="type-toggles">
			<button
				class="type-toggle"
				class:active={localTypes.person}
				onclick={() => toggleType('person')}
			>
				<span class="type-dot" style="background: #7c6bc4"></span>
				People
			</button>
			<button
				class="type-toggle"
				class:active={localTypes.place}
				onclick={() => toggleType('place')}
			>
				<span class="type-dot" style="background: #4a9e7a"></span>
				Places
			</button>
			<button
				class="type-toggle"
				class:active={localTypes.topic}
				onclick={() => toggleType('topic')}
			>
				<span class="type-dot" style="background: #c49a3c"></span>
				Topics
			</button>
		</div>
	</div>

	<div class="control-group">
		<span class="control-label">Date range</span>
		<div class="date-row">
			<input
				type="date"
				class="date-input"
				bind:value={dateFrom}
				onchange={handleDateChange}
			/>
			<span class="date-separator">&ndash;</span>
			<input
				type="date"
				class="date-input"
				bind:value={dateTo}
				onchange={handleDateChange}
			/>
		</div>
	</div>

	<div class="control-group">
		<span class="control-label">Min. connections <span class="weight-value">{localMinWeight}</span></span>
		<input
			type="range"
			class="weight-slider"
			min="1"
			max={Math.max(2, maxWeight)}
			bind:value={localMinWeight}
			oninput={handleWeightChange}
		/>
	</div>

	{#if hasNonDefaults}
		<button class="reset-btn" onclick={reset}>Reset</button>
	{/if}
</div>

<style>
	.graph-controls {
		display: flex;
		align-items: center;
		gap: 24px;
		flex-wrap: wrap;
		padding: 12px 16px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.control-group {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.control-label {
		font-size: 12px;
		font-weight: 600;
		color: var(--color-text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		white-space: nowrap;
	}

	.type-toggles {
		display: flex;
		gap: 4px;
	}

	.type-toggle {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 4px 10px;
		border-radius: 100px;
		border: 1px solid var(--color-border);
		background: var(--color-surface);
		font-size: 13px;
		font-weight: 500;
		color: var(--color-text-tertiary);
		transition: all 0.15s ease;
	}

	.type-toggle:hover {
		color: var(--color-text-secondary);
		border-color: var(--color-text-tertiary);
	}

	.type-toggle.active {
		color: var(--color-text);
		border-color: var(--color-text-secondary);
		background: var(--color-bg);
	}

	.type-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		display: inline-block;
	}

	.date-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.date-input {
		padding: 4px 8px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 13px;
		background: var(--color-surface);
		color: var(--color-text);
		outline: none;
		transition: border-color 0.15s ease;
		width: 130px;
	}

	.date-input:focus {
		border-color: var(--color-accent);
	}

	.date-separator {
		color: var(--color-text-tertiary);
		font-size: 13px;
	}

	.weight-slider {
		width: 100px;
		accent-color: var(--color-accent);
	}

	.weight-value {
		font-weight: 700;
		color: var(--color-accent);
		font-size: 12px;
	}

	.reset-btn {
		background: none;
		border: none;
		color: var(--color-accent);
		font-size: 13px;
		font-weight: 500;
		padding: 4px 0;
		transition: color 0.15s ease;
	}

	.reset-btn:hover {
		color: var(--color-accent-dark);
	}
</style>
