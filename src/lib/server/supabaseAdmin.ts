import { createClient } from '@supabase/supabase-js';
import { PUBLIC_SUPABASE_URL } from '$env/static/public';
import { SUPABASE_SERVICE_ROLE_KEY } from '$env/static/private';

/**
 * Server-only Supabase client using the service role key — bypasses RLS
 * entirely. This exists for exactly one purpose right now: reading
 * `portal_credentials.password_hash` during login verification in
 * `/result/[id]/login/+server.ts`, which the RLS policy on that table
 * (0002_rls_policies.sql) deliberately does not expose to the anon client.
 *
 * NEVER import this from a `.svelte` file or anything that ships to the
 * browser — `$env/static/private` throws at build time if you try, which
 * is the actual guardrail here, not just convention.
 */
export const supabaseAdmin = createClient(PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
	auth: { autoRefreshToken: false, persistSession: false }
});
