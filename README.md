# tendercare-portal
Tendercare Comprehensive College — result/transcript portal and student directory (Svelte + Supabase rebuild)

## The student password: one value, set in one place

Every student's result page opens with the same password. It is the
`STUDENT_LOGIN_PASSWORD` environment setting -- in the deployment's environment
variables (Vercel) and, for local runs, in `.env`. Change it in those places and
every student's login changes at once. There is no database step and nothing
to re-run.

- The **student ID** still decides whose result opens: it must be in the
  hardcoded directory (`src/lib/students.ts`, all active students including the
  2026/27 intake). A right password with an unknown ID is refused.
- Spaces typed around the password are ignored; capital letters matter.
- While `STUDENT_LOGIN_PASSWORD` is **not** set, the portal falls back to the
  older check against `portal_credentials` in Supabase (which only knows the
  students that database knows). Set the variable and that fallback is no
  longer used.
- Test: `npx tsx scripts/tests/shared_password_test.ts`.

The standalone transcripts made by the report pipeline in `tendercare-teacher`
read the same `STUDENT_LOGIN_PASSWORD`, so portal and transcripts cannot disagree.

