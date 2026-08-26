import { createClient } from '@supabase/supabase-js';
import { PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';

// Read-only from this app's perspective — enforced by the "portal and
// public apps see active students only" RLS policy in tendercare-teacher's
// supabase/migrations/0002_rls_policies.sql. This client has no write
// access to students at all, regardless of what the app code does.
export const supabase = createClient(PUBLIC_SUPABASE_URL, PUBLIC_SUPABASE_ANON_KEY);
