<script lang="ts">
	import { onMount } from 'svelte';
	import { listDirectory, type DirectoryEntry } from '$lib/data';
	import Crest from '$lib/components/Crest.svelte';

	let students = $state<DirectoryEntry[]>([]);
	let loading = $state(true);
	let error = $state('');
	let search = $state('');

	onMount(async () => {
		try {
			students = await listDirectory();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load directory';
		} finally {
			loading = false;
		}
	});

	const filtered = $derived(
		search.trim()
			? students.filter(
					(s) =>
						s.full_name.toLowerCase().includes(search.trim().toLowerCase()) ||
						s.id.toLowerCase().includes(search.trim().toLowerCase())
				)
			: students
	);

	const byClass = $derived.by(() => {
		const groups = new Map<string, DirectoryEntry[]>();
		for (const s of filtered) {
			if (!groups.has(s.class_id)) groups.set(s.class_id, []);
			groups.get(s.class_id)!.push(s);
		}
		return groups;
	});
</script>

<svelte:head>
	<title>Student Directory — Tendercare Comprehensive College</title>
</svelte:head>

<div class="bg-crest-wrap" aria-hidden="true">
	<Crest class="bg-crest" size="min(1400px, 150vw)" />
</div>

<div class="directory-page">
	<header class="directory-header">
		<Crest class="directory-logo" size="4.25rem" />
		<h1>Student Directory</h1>
		<p>Search for a student to view their results.</p>
		<input
			type="text"
			placeholder="Search by name or ID…"
			bind:value={search}
			class="directory-search"
		/>
	</header>

	{#if error}
		<p class="directory-error">{error}</p>
	{:else if loading}
		<p class="directory-loading">Loading…</p>
	{:else}
		{#each [...byClass.entries()] as [classId, classStudents] (classId)}
			<section class="class-group">
				<h2>{classId} <span class="class-count">({classStudents.length})</span></h2>
				<div class="student-grid">
					{#each classStudents as s (s.id)}
						<a class="student-card" href="/result/{s.id}/">
							<span class="student-name">{s.full_name}</span>
							<span class="student-id">{s.id}</span>
						</a>
					{/each}
				</div>
			</section>
		{/each}
	{/if}
</div>

<style>
	/* Giant, feint, fixed background crest — matches the reference
	   student-directory.html's .bg-crest-wrap / .bg-crest treatment */
	:global(.bg-crest-wrap) {
		position: fixed;
		inset: 0;
		z-index: 0;
		pointer-events: none;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	:global(.bg-crest) {
		color: var(--color-purple-deep, #3a1a5c);
		opacity: 0.045;
	}

	.directory-page {
		position: relative;
		z-index: 1;
		max-width: 1000px;
		margin: 0 auto;
		padding: var(--space-8, 2rem) var(--space-5, 1.25rem);
		font-family: var(--font-sans, system-ui);
	}
	.directory-header {
		text-align: center;
		margin-bottom: var(--space-10, 2.5rem);
	}
	:global(.directory-logo) {
		color: var(--color-purple-deep, #3a1a5c);
		margin: 0 auto 0.6rem auto;
	}
	.directory-header p {
		opacity: 0.6;
		margin-bottom: var(--space-5, 1.25rem);
	}
	.directory-search {
		width: 100%;
		max-width: 420px;
		padding: 0.7rem 1rem;
		border-radius: 999px;
		border: 1px solid #ccc;
		font-size: 0.95rem;
	}
	.directory-error {
		text-align: center;
		color: #900;
	}
	.directory-loading {
		text-align: center;
		opacity: 0.6;
	}
	.class-group {
		margin-bottom: var(--space-8, 2rem);
	}
	.class-group h2 {
		font-family: var(--font-serif, serif);
		font-weight: 500;
		font-size: 1.1rem;
		margin-bottom: var(--space-3, 0.75rem);
		border-bottom: 1px solid #eee;
		padding-bottom: 0.4rem;
	}
	.class-count {
		font-weight: 400;
		opacity: 0.5;
		font-size: 0.9rem;
	}
	.student-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.6rem;
	}
	.student-card {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		padding: 0.7rem 0.9rem;
		border: 1px solid #eee;
		border-radius: 10px;
		text-decoration: none;
		color: inherit;
		transition: border-color 0.15s, transform 0.15s;
	}
	.student-card:hover {
		border-color: var(--color-purple, #6b46c1);
		transform: translateY(-1px);
	}
	.student-name {
		font-weight: 500;
		font-size: 0.9rem;
	}
	.student-id {
		font-size: 0.75rem;
		opacity: 0.5;
		font-family: var(--font-mono, monospace);
	}

	@media (max-width: 640px) {
		:global(.bg-crest) {
			height: 220vw !important;
		}
	}
</style>
