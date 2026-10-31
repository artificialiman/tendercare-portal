import { timingSafeEqual } from 'node:crypto';

/**
 * One password for every student's result page, with no database involved.
 *
 * The value comes from the STUDENT_LOGIN_PASSWORD environment setting (the
 * deployment's environment variables, or a local .env). Change it there and
 * every student's login changes at once -- no per-student rows to rewrite, no
 * script to re-run. The student ID still decides *whose* result opens: it must
 * be one of the students in the hardcoded directory (src/lib/students.ts).
 *
 * Kept free of SvelteKit imports so it can be tested on its own
 * (scripts/tests/shared_password_test.ts).
 */

/** The configured shared password, or null when none is set (or it is blank). */
export function configuredPassword(raw: string | undefined | null): string | null {
	const value = (raw ?? '').trim();
	return value.length > 0 ? value : null;
}

/** Constant-time string comparison, so the check does not leak how much matched. */
function sameText(a: string, b: string): boolean {
	const x = Buffer.from(a, 'utf8');
	const y = Buffer.from(b, 'utf8');
	// Compare against a padded copy so unequal lengths still take the same path.
	const len = Math.max(x.length, y.length, 1);
	const px = Buffer.alloc(len);
	const py = Buffer.alloc(len);
	x.copy(px);
	y.copy(py);
	return timingSafeEqual(px, py) && x.length === y.length;
}

/**
 * True only when the ID is a known student AND the typed password equals the
 * shared one. Surrounding spaces on what was typed are ignored (phones add
 * them); case and everything else must match exactly.
 */
export function verifySharedPassword(
	studentId: string,
	typed: string,
	shared: string,
	knownIds: ReadonlySet<string>
): boolean {
	const idOk = knownIds.has(studentId);
	const pwOk = sameText(typed.trim(), shared);
	return idOk && pwOk;
}
