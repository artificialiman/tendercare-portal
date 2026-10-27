import { STUDENTS, type DirectoryEntry } from '$lib/students';

export type { DirectoryEntry };

/**
 * Student directory. Reads the hardcoded list in $lib/students.ts -- no
 * database call, no network. Kept async so the directory page's existing
 * loading/error handling still works unchanged.
 */
export async function listDirectory(): Promise<DirectoryEntry[]> {
	return [...STUDENTS];
}
