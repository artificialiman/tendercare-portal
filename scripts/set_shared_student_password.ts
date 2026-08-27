/**
 * One-time (or re-run-anytime) admin script: sets the SAME password for
 * every active student's result-portal login, hashed with bcrypt before
 * it ever touches the database or a repo.
 *
 * This exists because a shared-password-per-role scheme was the explicit
 * ask — one password for every student — but the actual password value
 * needs to live in an environment variable / your shell history, never
 * committed as plaintext in a public repo. This script is that boundary:
 * it reads the real password from STUDENT_LOGIN_PASSWORD at run time,
 * hashes it, and writes only the hash to `portal_credentials`.
 *
 * Usage:
 *   STUDENT_LOGIN_PASSWORD=12345678 \
 *   PUBLIC_SUPABASE_URL=https://your-project.supabase.co \
 *   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key \
 *   npx tsx scripts/set_shared_student_password.ts
 *
 * Safe to re-run: upserts every active student's row, so changing the
 * shared password later is just re-running this with a new value — no
 * migration needed. When a real per-student password strategy is chosen,
 * this script gets replaced (not patched) by whatever generates those.
 */
import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

const password = process.env.STUDENT_LOGIN_PASSWORD;
const url = process.env.PUBLIC_SUPABASE_URL;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!password || !url || !serviceKey) {
	console.error(
		'Missing required env vars. Need STUDENT_LOGIN_PASSWORD, PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY.'
	);
	process.exit(1);
}

if (password.length < 6) {
	console.error('Refusing to set a password shorter than 6 characters.');
	process.exit(1);
}

const supabase = createClient(url, serviceKey);

async function main() {
	const { data: students, error } = await supabase
		.from('students')
		.select('id')
		.eq('active', true);

	if (error) {
		console.error('Failed to load roster:', error.message);
		process.exit(1);
	}
	if (!students?.length) {
		console.error('No active students found — nothing to do.');
		process.exit(1);
	}

	const hash = await bcrypt.hash(password!, 10);
	const rows = students.map((s) => ({ student_id: s.id, password_hash: hash }));

	const { error: upsertError } = await supabase
		.from('portal_credentials')
		.upsert(rows, { onConflict: 'student_id' });

	if (upsertError) {
		console.error('Failed to write credentials:', upsertError.message);
		process.exit(1);
	}

	console.log(`Set shared password for ${rows.length} active students.`);
}

main();
