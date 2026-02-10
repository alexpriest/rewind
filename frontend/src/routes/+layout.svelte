<script lang="ts">
	import type { Snippet } from 'svelte';
	import '../app.css';
	import { page } from '$app/state';

	let { children }: { children: Snippet } = $props();

	const navItems = [
		{ href: '/', label: 'Home', icon: '\u25C9' },
		{ href: '/import', label: 'Import', icon: '\u2191' },
		{ href: '/search', label: 'Search', icon: '⌗' },
		{ href: '/explore', label: 'Explore', icon: '\u25CE' },
		{ href: '/reports', label: 'Reports', icon: '\u2756' }
	];
</script>

<svelte:head>
	<title>Rewind</title>
</svelte:head>

<div class="app">
	<nav class="sidebar">
		<div class="logo">
			<span class="logo-text">Rewind</span>
		</div>
		<ul class="nav-list">
			{#each navItems as item}
				<li>
					<a
						href={item.href}
						class="nav-link"
						class:active={item.href === '/'
							? page.url.pathname === '/'
							: page.url.pathname.startsWith(item.href)}
					>
						<span class="nav-icon">{item.icon}</span>
						<span class="nav-label">{item.label}</span>
					</a>
				</li>
			{/each}
		</ul>
	</nav>
	<main class="content">
		{@render children()}
	</main>
</div>

<style>
	.app {
		display: flex;
		min-height: 100vh;
	}

	.sidebar {
		width: 200px;
		background: var(--color-surface);
		border-right: 1px solid var(--color-border);
		padding: 24px 16px;
		position: fixed;
		top: 0;
		left: 0;
		bottom: 0;
		display: flex;
		flex-direction: column;
	}

	.logo {
		margin-bottom: 32px;
		padding: 0 8px;
	}

	.logo-text {
		font-size: 22px;
		font-weight: 700;
		color: var(--color-accent);
		letter-spacing: -0.5px;
	}

	.nav-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.nav-link {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border-radius: var(--radius-sm);
		color: var(--color-text-secondary);
		font-size: 14px;
		font-weight: 500;
		transition: all 0.15s ease;
	}

	.nav-link:hover {
		background: var(--color-bg);
		color: var(--color-text);
	}

	.nav-link.active {
		background: var(--color-accent-light);
		color: var(--color-accent-dark);
	}

	.nav-icon {
		font-size: 16px;
		width: 20px;
		text-align: center;
	}

	.content {
		flex: 1;
		margin-left: 200px;
		padding: 32px 40px;
		max-width: 1200px;
	}
</style>
