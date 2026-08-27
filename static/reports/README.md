# Static report pages

Generated ahead of time by the report-generation pipeline (schema +
Jinja2 template + generate.py) -- not fetched from Supabase, not built
at request time. `src/routes/result/[id]/+page.svelte` serves these
directly (same-origin, no network dependency) once the password check
in `result/[id]/login` succeeds.

Right now this only has one example per class-arm (12 files, from the
pipeline's demo run) -- two use real digitized scores (TCH-2025-032,
TCH-2025-214), the rest (TCH-0000-*) are clearly-labeled placeholder
data, never real student IDs. Populating this folder for every actual
student is the generation script's job (run against real per-student
JSON files, not built here), not something to hand-author one file at
a time.

See the pipeline itself (schema/, templates/, generate.py) and the
crosscheck report for the full picture.
