<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getStudent, getScores, getClassSize, type StudentScore } from '$lib/data';
	import { grade, gradeClass, REMARKS } from '$lib/grading';

	const studentId = $derived(page.params.id);

	let loading = $state(true);
	let notFound = $state(false);
	let student = $state<{ id: string; full_name: string; class_id: string } | null>(null);
	let classSize = $state(0);
	let scores = $state<StudentScore[]>([]);
	let activeTerm = $state<string>('');

	// NOTE: auth removed for now, per instruction — this route is open. A
	// real access-control decision (per-student password, staff-issued
	// link, etc.) still needs to be made before this goes in front of
	// real users; see tendercare-teacher's README for why the *previous*
	// approach (one hardcoded password shared by the entire school,
	// visible in view-source) wasn't something to carry forward as-is.

	onMount(async () => {
		if (!studentId) return;
		loading = true;
		notFound = false;
		const s = await getStudent(studentId);
		if (!s) {
			notFound = true;
			loading = false;
			return;
		}
		student = s;
		[classSize, scores] = await Promise.all([getClassSize(s.class_id), getScores(studentId)]);
		const terms = [...new Set(scores.map((sc) => sc.term_id))].sort();
		activeTerm = terms[terms.length - 1] ?? '';
		loading = false;
	});

	const termsAvailable = $derived([...new Set(scores.map((s) => s.term_id))].sort());
	const termScores = $derived(scores.filter((s) => s.term_id === activeTerm));
	const rows = $derived(
		termScores.map((s) => {
			const total = s.ca !== null && s.exam !== null ? s.ca + s.exam : null;
			const g = grade(total);
			return { ...s, total, grade: g, remark: REMARKS[g] ?? '—' };
		})
	);
	const totals = $derived.by(() => {
		const valid = rows.filter((r) => r.total !== null).map((r) => r.total as number);
		if (!valid.length) return { total: 0, avg: 0, high: 0, low: 0 };
		const total = valid.reduce((a, b) => a + b, 0);
		return {
			total,
			avg: Math.round((total / valid.length) * 10) / 10,
			high: Math.max(...valid),
			low: Math.min(...valid)
		};
	});
</script>

<svelte:head>
	<title>{student ? `${student.full_name} — Results — TCC` : 'Results — Tendercare Comprehensive College'}</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

{#if loading}
	<div class="loading-state">Loading…</div>
{:else if notFound}
	<div class="loading-state">
		<p>No student found for ID <strong>{studentId}</strong>.</p>
		<a href="/">Back to directory</a>
	</div>
{:else if student}
	<div id="resultPage">
		<nav class="result-nav">
			<div class="result-nav-left">
				<div class="result-nav-logo"><span>TCC</span></div>
				<div class="result-nav-title">Academic Results</div>
			</div>
			<div class="result-nav-actions">
				<button class="nav-btn nav-btn--print" onclick={() => window.print()}>Print / PDF</button>
				<a class="nav-btn" href="/">Directory</a>
			</div>
		</nav>

		<div class="sheet-wrap">
			<div class="sheet">
				<div class="letterhead">
					<div class="logo-slot"><span>School<br />Logo</span></div>
					<div class="school-identity">
						<div class="school-name">Tendercare Comprehensive College</div>
						<div class="school-address">Lagos, Nigeria</div>
						<div class="school-tagline">"Raising minds. Shaping futures."</div>
					</div>
					<div class="stamp-slot"><span>Official<br />Stamp</span></div>
				</div>

				<div class="report-bar">Academic Progress Report &nbsp;·&nbsp; 2024/2025 Session</div>

				<div class="meta">
					<div class="photo-box">
						<div class="photo-ph">
							<div class="photo-ph-circle"></div>
							<div class="photo-ph-bar"></div>
							<div class="photo-ph-bar" style="width:36px;"></div>
						</div>
					</div>
					<div class="meta-grid">
						<div class="mf"><span class="ml">Student Name</span><span class="mv big">{student.full_name}</span></div>
						<div class="mf"><span class="ml">Student ID</span><span class="mv">{student.id}</span></div>
						<div class="mf"><span class="ml">Class</span><span class="mv">{student.class_id}</span></div>
						<div class="mf"><span class="ml">Session</span><span class="mv">2024/2025</span></div>
						<div class="mf"><span class="ml">Class Teacher</span><span class="mv">_________________</span></div>
						<div class="mf"><span class="ml">No. in Class</span><span class="mv">{classSize}</span></div>
					</div>
				</div>

				{#if termsAvailable.length > 1}
					<div class="term-tabs">
						{#each termsAvailable as t (t)}
							<button
								class="term-tab"
								class:active={activeTerm === t}
								onclick={() => (activeTerm = t)}>{t}</button
							>
						{/each}
					</div>
				{/if}

				{#if rows.length === 0}
					<div class="panel-locked">
						<div class="lock-icon">📋</div>
						<div class="lock-title">No results uploaded yet</div>
						<div class="lock-sub">Scores will appear here once submitted.</div>
					</div>
				{:else}
					<div class="panel active">
						<div class="scores">
							<table>
								<thead>
									<tr>
										<th style="width:32%;">Subject</th>
										<th>CA <span style="font-size:0.58rem;opacity:0.7;font-weight:400;">/30</span></th>
										<th>Exam <span style="font-size:0.58rem;opacity:0.7;font-weight:400;">/70</span></th>
										<th>Total <span style="font-size:0.58rem;opacity:0.7;font-weight:400;">/100</span></th>
										<th>Grade</th>
										<th>Remark</th>
									</tr>
								</thead>
								<tbody>
									{#each rows as r (r.subject)}
										<tr>
											<td>{r.subject}</td>
											<td>{r.ca ?? '—'}</td>
											<td>{r.exam ?? '—'}</td>
											<td>{r.total ?? '—'}</td>
											<td><span class="g {gradeClass(r.grade)}">{r.grade}</span></td>
											<td>{r.remark}</td>
										</tr>
									{/each}
								</tbody>
								<tfoot>
									<tr>
										<td colspan="2" style="text-align:left;font-size:0.65rem;letter-spacing:0.06em;text-transform:uppercase;">
											Total / Average
										</td>
										<td>{totals.avg}</td>
										<td>{totals.total}</td>
										<td colspan="2">Position: —</td>
									</tr>
								</tfoot>
							</table>
						</div>

						<div class="grade-key">
							<span class="gk-label">Grade Key:</span>
							<span class="gk-item"><span class="g g-a1">A1</span> 75–100</span>
							<span class="gk-item"><span class="g g-b2">B2</span> 70–74</span>
							<span class="gk-item"><span class="g g-b3">B3</span> 65–69</span>
							<span class="gk-item"><span class="g g-c4">C4</span> 60–64</span>
							<span class="gk-item"><span class="g g-c5">C5</span> 55–59</span>
							<span class="gk-item"><span class="g g-c6">C6</span> 50–54</span>
							<span class="gk-item"><span class="g g-d7">D7</span> 45–49</span>
							<span class="gk-item"><span class="g g-e8">E8</span> 40–44</span>
							<span class="gk-item"><span class="g g-f9">F9</span> 0–39</span>
						</div>

						<div class="stats">
							<div class="stat"><div class="stat-l">Total Score</div><div class="stat-v">{totals.total}</div></div>
							<div class="stat"><div class="stat-l">Average</div><div class="stat-v">{totals.avg}</div></div>
							<div class="stat"><div class="stat-l">Highest</div><div class="stat-v">{totals.high}</div></div>
							<div class="stat"><div class="stat-l">Lowest</div><div class="stat-v">{totals.low}</div></div>
						</div>

						<div class="comments">
							<div class="cb">
								<span class="cb-label">Class Teacher's Comment</span>
								<div class="cb-box cb-box--readonly">Not yet entered.</div>
								<div class="sig">
									<div class="sig-line"><span>Signature</span></div>
									<span class="sig-date">Date: ___________</span>
								</div>
							</div>
							<div class="cb">
								<span class="cb-label">Principal's Comment</span>
								<div class="cb-box cb-box--readonly">Not yet entered.</div>
								<div class="sig">
									<div class="sig-line"><span>Signature</span></div>
									<span class="sig-date">Date: ___________</span>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<div class="sheet-foot">
					<span class="sheet-foot-school">Tendercare Comprehensive College</span>
					<span class="sheet-foot-ref">2024/2025 · {activeTerm}</span>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.loading-state {
		max-width: 480px;
		margin: 4rem auto;
		text-align: center;
		font-family: var(--font-sans, system-ui);
	}
	.cb-box--readonly {
		min-height: 3.5rem;
		border: 1px solid #ddd;
		border-radius: 6px;
		padding: 0.5rem;
		font-size: 0.85rem;
		opacity: 0.5;
		font-style: italic;
	}
	.term-tabs .term-tab.active {
		font-weight: 600;
	}

	/* Ported from the original result.html report-card design */

    :root {
      --purple:       #5B2D8E;
      --purple-deep:  #3A1A5C;
      --purple-light: #C4A8E0;
      --purple-ghost: #F0E8FA;
      --cream:        #F8F4EC;
      --cream-warm:   #F0E8D8;
      --cream-deep:   #E4D8C4;
      --ink:          #1A1020;
      --ash:          #A8A8B0;
      --ash-light:    #E8E8F0;
      --white:        #FFFFFF;
      --font-serif:   'Cormorant Garamond', Georgia, serif;
      --font-sans:    'DM Sans', system-ui, sans-serif;
    }

    /* ═══════════════════════
       RESULT PAGE
    ═══════════════════════ */
    #resultPage { display: none; }

    .result-nav {
      background: var(--purple-deep);
      padding: 1rem 2rem;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 50;
    }
    .result-nav-left { display: flex; align-items: center; gap: 0.75rem; }
    .result-nav-logo {
      width: 34px; height: 34px;
      border: 1px dashed rgba(196,168,224,0.3); border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
    }
    .result-nav-logo span { font-size: 0.42rem; color: var(--purple-light); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; text-align: center; line-height: 1.4; }
    .result-nav-title { font-family: var(--font-serif); font-size: 1rem; color: var(--white); }
    .result-nav-actions { display: flex; gap: 0.75rem; }
    .nav-btn {
      font-family: var(--font-sans); font-size: 0.72rem; font-weight: 600;
      padding: 0.4rem 0.9rem; border-radius: 6px; cursor: pointer;
      letter-spacing: 0.06em; text-transform: uppercase; border: none;
      transition: background 0.2s;
    }
    .nav-btn--print { background: var(--purple); color: var(--white); }
    .nav-btn--print:hover { background: #7B4DB0; }
    .nav-btn--lock { background: rgba(231,76,60,0.15); border: 1px solid rgba(231,76,60,0.3); color: #f1948a; }
    .nav-btn--lock:hover { background: rgba(231,76,60,0.25); }

    /* Sheet */
    .sheet-wrap { padding: 2rem 1rem 4rem; }
    .sheet {
      max-width: 820px; margin: 0 auto;
      background: var(--white);
      border: 1px solid var(--cream-deep);
      border-radius: 4px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.12);
      overflow: hidden;
    }

    /* Letterhead */
    .letterhead {
      padding: 1.75rem 2.5rem 1.25rem;
      border-bottom: 3px solid var(--purple);
      display: grid; grid-template-columns: 72px 1fr 72px;
      align-items: center; gap: 1.5rem;
      background: var(--cream);
    }
    .logo-slot, .stamp-slot {
      width: 72px; height: 72px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
    }
    .logo-slot { border: 1.5px dashed var(--purple-light); background: var(--purple-ghost); }
    .logo-slot span { font-size: 0.55rem; text-align: center; color: var(--purple); font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; line-height: 1.5; padding: 0 6px; }
    .stamp-slot { border: 1.5px dashed var(--ash); background: var(--ash-light); }
    .stamp-slot span { font-size: 0.55rem; text-align: center; color: var(--ash); font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; line-height: 1.5; padding: 0 6px; }
    .school-identity { text-align: center; }
    .school-name { font-family: var(--font-serif); font-size: 1.6rem; font-weight: 600; color: var(--purple-deep); letter-spacing: 0.02em; line-height: 1.2; }
    .school-address { font-size: 0.72rem; color: var(--ash); margin-top: 0.25rem; }
    .school-tagline { font-family: var(--font-serif); font-style: italic; font-size: 0.82rem; color: var(--purple); margin-top: 0.2rem; opacity: 0.75; }

    .report-bar {
      background: var(--purple); color: var(--white);
      text-align: center; padding: 0.55rem 2rem;
      font-size: 0.65rem; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase;
    }

    /* Meta */
    .meta {
      padding: 1.25rem 2.5rem;
      background: var(--cream); border-bottom: 1px solid var(--cream-deep);
      display: grid; grid-template-columns: 80px 1fr; gap: 1.5rem; align-items: start;
    }
    .photo-box {
      width: 80px; height: 100px;
      border: 1.5px solid var(--cream-deep); border-radius: 4px;
      overflow: hidden; background: var(--ash-light);
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .photo-ph { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; width: 100%; height: 100%; }
    .photo-ph-circle { width: 32px; height: 32px; border-radius: 50%; background: rgba(91,45,142,0.15); }
    .photo-ph-bar { width: 44px; height: 4px; border-radius: 2px; background: rgba(91,45,142,0.1); }
    .meta-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 0.65rem 1.5rem; }
    .mf { display: flex; flex-direction: column; gap: 1px; }
    .ml { font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: var(--ash); }
    .mv { font-size: 0.875rem; font-weight: 500; border-bottom: 1px solid var(--cream-deep); padding-bottom: 2px; min-height: 1.35rem; color: var(--ink); }
    .mv.big { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600; color: var(--purple-deep); }

    /* Term tabs */
    .term-tabs { display: flex; border-bottom: 1px solid var(--cream-deep); background: var(--cream-warm); }
    .term-tab {
      flex: 1; text-align: center; padding: 0.7rem 0.5rem;
      font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
      cursor: pointer; border: none; background: transparent; font-family: var(--font-sans);
      color: var(--ash); border-bottom: 3px solid transparent; transition: all 0.2s;
    }
    .term-tab.active { color: var(--purple); border-bottom-color: var(--purple); background: var(--white); }
    .term-tab.locked { opacity: 0.4; cursor: not-allowed; }

    /* Panels */
    .panel { display: none; }
    .panel.active { display: block; }
    .panel-locked { display: none; padding: 3rem 2rem; text-align: center; }
    .panel-locked.active { display: block; }
    .lock-icon { width: 52px; height: 52px; border-radius: 50%; background: var(--ash-light); display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; font-size: 1.4rem; }
    .lock-title { font-family: var(--font-serif); font-size: 1.15rem; color: var(--ink); margin-bottom: 0.4rem; }
    .lock-sub { font-size: 0.78rem; color: var(--ash); max-width: 28ch; margin: 0 auto; line-height: 1.65; }

    /* Scores table */
    .scores { padding: 1.5rem 2.5rem; }
    table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
    thead tr { background: var(--purple); color: var(--white); }
    thead th { padding: 0.55rem 0.65rem; text-align: center; font-weight: 600; font-size: 0.65rem; letter-spacing: 0.08em; text-transform: uppercase; white-space: nowrap; }
    thead th:first-child { text-align: left; }
    tbody tr:nth-child(even) { background: var(--cream); }
    tbody td { padding: 0.5rem 0.65rem; text-align: center; border-bottom: 1px solid var(--cream-deep); }
    tbody td:first-child { text-align: left; font-weight: 500; }
    tfoot tr { background: var(--purple-deep); }
    tfoot td { padding: 0.55rem 0.65rem; font-weight: 600; font-size: 0.75rem; color: var(--white); border: none; text-align: center; }
    tfoot td:first-child { text-align: left; }

    .g { display: inline-block; padding: 2px 7px; border-radius: 3px; font-weight: 700; font-size: 0.72rem; }
    .g-a1 { background:#D4EDDA; color:#155724; } .g-b2 { background:#CCE5FF; color:#004085; }
    .g-b3 { background:#D6EAF8; color:#1A5276; } .g-c4 { background:#FFF3CD; color:#856404; }
    .g-c5 { background:#FFF8E1; color:#7B6200; } .g-c6 { background:#FDF3E3; color:#7E5109; }
    .g-d7 { background:#FDEBD0; color:#935116; } .g-e8 { background:#FDEDEC; color:#922B21; }
    .g-f9 { background:#F9EBEA; color:#7B241C; } .g-em { background:var(--ash-light); color:var(--ash); }

    /* Grade key */
    .grade-key {
      margin: 0 2.5rem 1.25rem; padding: 0.65rem 1rem;
      background: var(--cream); border: 1px solid var(--cream-deep); border-radius: 4px;
      display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; align-items: center; font-size: 0.68rem;
    }
    .gk-label { font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ash); }
    .gk-item { display: flex; align-items: center; gap: 3px; }

    /* Stats */
    .stats { margin: 0 2.5rem 1.25rem; display: grid; grid-template-columns: repeat(4,1fr); gap: 0.65rem; }
    .stat { background: var(--cream); border: 1px solid var(--cream-deep); border-radius: 4px; padding: 0.65rem 0.85rem; text-align: center; }
    .stat-l { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ash); font-weight: 600; }
    .stat-v { font-family: var(--font-serif); font-size: 1.5rem; font-weight: 600; color: var(--purple-deep); line-height: 1.1; }

    /* Comments */
    .comments {
      padding: 1.1rem 2.5rem 1.5rem; border-top: 1px solid var(--cream-deep);
      display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;
    }
    .cb { display: flex; flex-direction: column; gap: 0.35rem; }
    .cb-label { font-size: 0.62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: var(--ash); }
    .cb-box {
      border: 1px solid var(--cream-deep); border-radius: 4px; padding: 0.55rem 0.7rem;
      min-height: 56px; font-family: var(--font-serif); font-size: 0.875rem; font-style: italic;
      color: var(--ink); background: var(--cream); width: 100%;
      line-height: 1.6; resize: none;
    }
    .cb-box::placeholder { color: var(--ash); }
    .sig { display: flex; align-items: flex-end; gap: 1rem; margin-top: 0.35rem; }
    .sig-line { flex: 1; border-bottom: 1px solid var(--ink); height: 32px; position: relative; }
    .sig-line span { position: absolute; bottom: -17px; left: 0; font-size: 0.58rem; color: var(--ash); text-transform: uppercase; letter-spacing: 0.07em; }
    .sig-date { font-size: 0.65rem; color: var(--ash); white-space: nowrap; padding-bottom: 2px; }

    /* Footer */
    .sheet-foot {
      padding: 0.65rem 2.5rem; background: var(--purple-deep);
      display: flex; align-items: center; justify-content: space-between;
    }
    .sheet-foot-school { font-family: var(--font-serif); font-size: 0.8rem; color: var(--purple-light); font-style: italic; }
    .sheet-foot-ref { font-size: 0.6rem; color: rgba(196,168,224,0.4); letter-spacing: 0.1em; text-transform: uppercase; }

    @media print {
      #resultPage { display: block !important; }
      .result-nav, .sheet-wrap > *:not(.sheet) { display: none; }
      .sheet { box-shadow: none; }
      .cb-box { border: none; background: transparent; }
    }
</style>
