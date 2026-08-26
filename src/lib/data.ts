import { supabase } from '$lib/supabase';

export interface StudentScore {
	subject: string;
	term_id: string;
	ca: number | null;
	exam: number | null;
}

export interface StudentProfile {
	id: string;
	full_name: string;
	class_id: string;
}

export async function getStudent(id: string): Promise<StudentProfile | null> {
	const { data, error } = await supabase
		.from('students')
		.select('id, full_name, class_id')
		.eq('id', id)
		.eq('active', true)
		.single();
	if (error) return null;
	return data as StudentProfile;
}

export async function getScores(studentId: string): Promise<StudentScore[]> {
	const { data, error } = await supabase
		.from('scores')
		.select('term_id, ca, exam, subjects(name)')
		.eq('student_id', studentId);
	if (error) throw error;
	return (data ?? []).map((row: any) => ({
		subject: row.subjects?.name ?? 'Unknown subject',
		term_id: row.term_id,
		ca: row.ca,
		exam: row.exam
	}));
}

export async function getClassSize(classId: string): Promise<number> {
	const { count, error } = await supabase
		.from('students')
		.select('id', { count: 'exact', head: true })
		.eq('class_id', classId)
		.eq('active', true);
	if (error) return 0;
	return count ?? 0;
}

export interface DirectoryEntry {
	id: string;
	full_name: string;
	class_id: string;
}

export async function listDirectory(): Promise<DirectoryEntry[]> {
	const { data, error } = await supabase
		.from('students')
		.select('id, full_name, class_id')
		.eq('active', true)
		.order('class_id')
		.order('id');
	if (error) throw error;
	return data as DirectoryEntry[];
}
