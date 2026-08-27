import { json } from '@sveltejs/kit';
import bcrypt from 'bcryptjs';
import { supabaseAdmin } from '$lib/server/supabaseAdmin';
import type { RequestHandler } from './$types';

/**
 * Verifies a student's result-page password. Runs server-side only — the
 * service-role client here can read `portal_credentials.password_hash`,
 * which RLS deliberately hides from the browser-side anon client (see
 * 0002_rls_policies.sql's comment on that table).
 *
 * Current password policy: every student shares the same password value
 * (set once by an admin script — see
 * scripts/set_shared_student_password.ts), so this endpoint is really
 * checking "does this ID exist and is the shared password correct" rather
 * than verifying a per-student secret. The student ID itself is still the
 * thing that scopes access to *that* student's own result — this is not a
 * single door that opens every record with no ID at all.
 *
 * This is an interim measure, not the final access-control design — a
 * real per-student or per-family credential is expected to replace it
 * once that decision is made (see the removed-auth note this file
 * replaces in +page.svelte's history).
 */
export const POST: RequestHandler = async ({ params, request }) => {
	const studentId = params.id;
	const { password } = await request.json();

	if (!studentId || typeof password !== 'string' || !password) {
		return json({ ok: false, error: 'Missing student ID or password.' }, { status: 400 });
	}

	const { data: student } = await supabaseAdmin
		.from('students')
		.select('id')
		.eq('id', studentId)
		.eq('active', true)
		.single();

	if (!student) {
		// Same generic error as a wrong password — don't reveal whether
		// the ID exists to an unauthenticated caller.
		return json({ ok: false, error: 'Incorrect student ID or password.' }, { status: 401 });
	}

	const { data: cred } = await supabaseAdmin
		.from('portal_credentials')
		.select('password_hash')
		.eq('student_id', studentId)
		.single();

	if (!cred) {
		return json(
			{ ok: false, error: 'No password set for this student yet — contact the school office.' },
			{ status: 401 }
		);
	}

	const valid = await bcrypt.compare(password, cred.password_hash);
	if (!valid) {
		return json({ ok: false, error: 'Incorrect student ID or password.' }, { status: 401 });
	}

	await supabaseAdmin
		.from('portal_credentials')
		.update({ last_login_at: new Date().toISOString() })
		.eq('student_id', studentId);

	return json({ ok: true });
};
