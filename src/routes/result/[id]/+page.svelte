<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import Crest from '$lib/components/Crest.svelte';

	const studentId = $derived(page.params.id);

	let loading = $state(true);
	let notFound = $state(false);
	let redirecting = $state(false);

	// Password gate — verified server-side against portal_credentials via
	// /result/[id]/login (see that route's comment for the current
	// shared-password policy and why it replaced the fully-open version
	// that used to be here, and tendercare-teacher's README for why the
	// version before *that* — one password hardcoded in view-source —
	// wasn't something to carry forward as-is either).
	let unlocked = $state(false);
	let passwordInput = $state('');
	let checkingPassword = $state(false);
	let passwordError = $state('');

	const SESSION_KEY = $derived(studentId ? `tc-portal-unlocked:${studentId}` : '');

	onMount(() => {
		if (studentId && sessionStorage.getItem(SESSION_KEY) === '1') {
			unlocked = true;
			void loadResult();
		}
	});

	async function handleUnlock(e: SubmitEvent) {
		e.preventDefault();
		if (!studentId) return;
		checkingPassword = true;
		passwordError = '';
		try {
			const res = await fetch(`/result/${studentId}/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ password: passwordInput })
			});
			const body = await res.json();
			if (!body.ok) {
				passwordError = body.error ?? 'Incorrect student ID or password.';
				return;
			}
			sessionStorage.setItem(SESSION_KEY, '1');
			unlocked = true;
			await loadResult();
		} finally {
			checkingPassword = false;
		}
	}

	/**
	 * Results are static and hardcoded in the repo, not a Supabase query.
	 * This used to call getStudent/getScores/getClassSize (live reads
	 * against the students/scores tables) and re-render the transcript
	 * from that data in Svelte. Per the antifail doctrine, that's exactly
	 * backwards for this piece: a full transcript is a "heavy report
	 * file," not something worth a network round-trip on every view,
	 * especially for a demographic with slow/unreliable connections.
	 *
	 * The actual report pages are generated ahead of time by the Python
	 * pipeline (schema + Jinja2 template + generate.py, see
	 * tendercare-teacher's handoff notes / the crosscheck doc) and land
	 * as static files in this repo's static/reports/ directory -- fully
	 * self-contained HTML, including their own crest watermark and
	 * teacher/principal remark sections, no further data fetch needed.
	 * This route's job, once the password check above succeeds, is only
	 * to hand the browser off to that static file -- same-origin, no
	 * external network call, no database read.
	 *
	 * static/reports/ only has a handful of example files in it right
	 * now (one per class-arm, from the pipeline's demo run). Populating
	 * it for every real student is the generation script's job, not
	 * this route's -- this just wires up where the result goes once it
	 * exists.
	 */
	async function loadResult() {
		if (!studentId) return;
		loading = true;
		notFound = false;
		const res = await fetch(`/reports/${studentId}.html`, { method: 'HEAD' });
		if (!res.ok) {
			notFound = true;
			loading = false;
			return;
		}
		redirecting = true;
		window.location.href = `/reports/${studentId}.html`;
	}
</script>

<svelte:head>
	<title>Results — Tendercare Comprehensive College</title>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

{#if !unlocked}
	<div class="unlock-page">
		<div class="unlock-card">
			<Crest size="3rem" class="unlock-crest" />
			<h1>Student ID: {studentId}</h1>
			<p>Enter your result password to continue.</p>
			<form onsubmit={handleUnlock}>
				<input
					type="password"
					placeholder="Password"
					bind:value={passwordInput}
					required
					autocomplete="current-password"
				/>
				{#if passwordError}
					<p class="unlock-error" role="alert">{passwordError}</p>
				{/if}
				<button type="submit" disabled={checkingPassword}>
					{checkingPassword ? 'Checking…' : 'View result'}
				</button>
			</form>
		</div>
	</div>
{:else if loading}
	<div class="loading-state">Loading…</div>
{:else if redirecting}
	<div class="loading-state">Opening your result…</div>
{:else if notFound}
	<div class="loading-state">
		<p>No result file found yet for ID <strong>{studentId}</strong>.</p>
		<p style="opacity:0.6; font-size: 0.9em;">
			The static report for this student hasn't been generated yet -- see
			the report-generation pipeline (schema + template + generate.py).
		</p>
		<a href="/">Back to directory</a>
	</div>
{/if}

<style>
	.loading-state {
		max-width: 480px;
		margin: 4rem auto;
		text-align: center;
		font-family: var(--font-sans, system-ui);
	}
	.unlock-page {
		min-height: 100dvh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1.5rem;
		font-family: var(--font-sans, system-ui);
	}
	.unlock-card {
		width: 100%;
		max-width: 340px;
		padding: 2rem;
		border: 1px solid var(--cream-deep, #eee);
		border-radius: 12px;
		text-align: center;
	}
	:global(.unlock-crest) {
		color: var(--purple-deep, #3a1a5c);
		margin: 0 auto 0.75rem auto;
	}
	.unlock-card h1 {
		font-size: 1rem;
		font-family: var(--font-serif, serif);
		margin: 0 0 0.35rem;
	}
	.unlock-card p {
		font-size: 0.85rem;
		opacity: 0.65;
		margin: 0 0 1.25rem;
	}
	.unlock-card form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.unlock-card input {
		padding: 0.6rem 0.8rem;
		border: 1px solid #ccc;
		border-radius: 8px;
		font-size: 0.95rem;
		text-align: center;
	}
	.unlock-card button {
		padding: 0.65rem;
		border-radius: 8px;
		border: none;
		background: var(--purple, #6b46c1);
		color: white;
		font-weight: 600;
		cursor: pointer;
	}
	.unlock-card button:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.unlock-error {
		color: #900;
		font-size: 0.82rem;
		margin: 0;
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
    /* NOTE: this component was ported from a static multi-section HTML
       page where #resultPage was one of several panels toggled by JS,
       with `display:none` as the default and a `@media print { display:
       block }` override to reveal it only when printing. That's why the
       result sheet used to disappear or fail to render on screen and in
       PDF export — Svelte's {#if student} already controls visibility,
       so no CSS-level display:none is needed or wanted here. */

    .result-nav {
      background: var(--purple-deep);
      padding: 1rem 2rem;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 50;
    }
    .result-nav-left { display: flex; align-items: center; gap: 0.75rem; }
    .result-nav-logo {
      color: var(--purple-light);
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
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
      position: relative;
      max-width: 820px; margin: 0 auto;
      background: var(--white);
      border: 1px solid var(--cream-deep);
      border-radius: 4px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.12);
      overflow: hidden;
      /* Without this, Chrome/Firefox print engines default to
         "conserve toner" and silently drop low-opacity background
         art like the watermark below when exporting to PDF. */
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    /* Letterhead-style watermark: a single crest centered on the
       *whole* sheet, sitting behind every section. Bands with their
       own solid fill (letterhead, report bar, table header/footer)
       naturally occlude it where they overlap, exactly like a real
       printed letterhead's security pattern — it only shows through
       the open white space (scores table body, stats, comments).
       That's why it's centered on .sheet as a whole rather than
       confined to the top band: pinned to just the header, it would
       sit entirely behind solid-color bands and never be visible at
       any opacity.
       Positioned `absolute` *inside* .sheet (part of the normal
       document flow) rather than `fixed` to the viewport — fixed-
       position layers are dropped or misplaced by most browsers'
       print/PDF renderers, which is the likely cause of the
       watermark "breaking" in PDF exports before. */
    .sheet-watermark {
      position: absolute;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      width: 480px;
      max-width: 85%;
      color: var(--purple-deep);
      opacity: 0.06;
      pointer-events: none;
      z-index: 0;
    }

    /* Everything else in the sheet sits above the watermark layer */
    .letterhead, .report-bar, .meta, .term-tabs, .panel, .panel-locked,
    .grade-key, .stats, .comments, .sheet-foot {
      position: relative;
      z-index: 1;
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
    .logo-slot {
      color: var(--purple-deep);
      padding: 8px;
      box-sizing: border-box;
    }
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
      .result-nav, .sheet-wrap > *:not(.sheet) { display: none; }
      .sheet {
        box-shadow: none;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
      .cb-box { border: none; background: transparent; }
      /* Force the faint watermark to print rather than being
         stripped as "background graphics" by a browser that defaults
         print requests to text-only. */
      .sheet-watermark {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
    }
</style>
