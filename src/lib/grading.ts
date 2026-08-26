/**
 * Ported verbatim from the original result.html's grade()/REMARKS logic —
 * this is genuinely reusable domain logic (the school's grading scale), not
 * a hardcoded piece of the demo shell it lived in.
 */

export const REMARKS: Record<string, string> = {
	A1: 'Excellent',
	B2: 'Very Good',
	B3: 'Good',
	C4: 'Credit',
	C5: 'Credit',
	C6: 'Credit',
	D7: 'Pass',
	E8: 'Pass',
	F9: 'Fail'
};

export function grade(total: number | null): string {
	if (total === null || Number.isNaN(total)) return '—';
	const n = Number(total);
	if (n >= 75) return 'A1';
	if (n >= 70) return 'B2';
	if (n >= 65) return 'B3';
	if (n >= 60) return 'C4';
	if (n >= 55) return 'C5';
	if (n >= 50) return 'C6';
	if (n >= 45) return 'D7';
	if (n >= 40) return 'E8';
	return 'F9';
}

export function gradeClass(g: string): string {
	return !g || g === '—' ? 'g-em' : 'g-' + g.toLowerCase();
}
