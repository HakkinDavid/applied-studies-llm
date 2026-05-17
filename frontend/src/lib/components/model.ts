export type HealthResponse = {
	status: string;
	message: string;
	ai_configured: boolean;
	model: string;
};

export type Material = {
	id: string;
	sha256: string;
	original_filename: string;
	stored_filename: string;
	extension: string;
	content_type: string | null;
	size_bytes: number;
	text_chars: number;
	reference_count: number;
	uploaded_at: string;
	duplicate: boolean;
	generated_questions: number;
	area?: string | null;
	subarea?: string | null;
	classification_summary?: string | null;
	knowledge_path?: string | null;
};

export type MaterialReference = {
	ref_id: string;
	page: number | null;
	excerpt: string;
	text?: string;
};

export type MaterialListResponse = {
	total: number;
	materials: Material[];
};

export type MaterialReferencesResponse = {
	material_id: string;
	total: number;
	references: MaterialReference[];
};

export type Question = {
	q: string;
	options: string[];
	answer: number;
	area?: string;
	subarea?: string | null;
	synthetic?: boolean;
	source_document_name?: string;
	source_ref_id?: string | null;
	source_page?: number | null;
	source_excerpt?: string | null;
	knowledge_path?: string;
};

export type QuestionBankResponse = {
	total: number;
	questions: Question[];
};

export type ForestLeaf = {
	id: string;
	name: string;
	description?: string;
	materials?: string[];
	question_count?: number;
};

export type ForestNode = {
	id: string;
	name: string;
	description?: string;
	leaves?: Record<string, ForestLeaf>;
};

export type ForestTree = {
	id: string;
	name: string;
	description?: string;
	nodes?: Record<string, ForestNode>;
};

export type KnowledgeForest = {
	trees?: Record<string, ForestTree>;
};

export type KnowledgeForestResponse = {
	total_trees: number;
	forest: KnowledgeForest;
};

export type StudyLevel = {
	name: string;
	questions: number;
	time: number;
};

export type ResultRow = {
	index: number;
	question: Question;
	userAnswer: string;
	correctAnswer: string;
	isCorrect: boolean;
};

export type UploadInput = {
	file: File | null;
	treeHint: string;
	numQuestions: number;
};

export const LEVELS: StudyLevel[] = [
	{ name: 'Ligero', questions: 15, time: 5 },
	{ name: 'Moderado', questions: 25, time: 10 },
	{ name: 'Intermedio', questions: 40, time: 15 },
	{ name: 'Avanzado', questions: 60, time: 25 },
	{ name: 'CENEVAL', questions: 140, time: 180 }
];

export const areaOf = (question: Question) => question.area?.trim() || 'Otro';
export const subareaOf = (question: Question) => question.subarea?.trim() || 'n/a';
export const pageLabel = (page: number | null | undefined) =>
	page ? `página ${page}` : 'sin página';
export const formatTime = (seconds: number) =>
	`${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
export const formatBytes = (bytes: number) =>
	bytes < 1024
		? `${bytes} B`
		: bytes < 1048576
			? `${(bytes / 1024).toFixed(1)} KB`
			: `${(bytes / 1048576).toFixed(1)} MB`;
export const formatDate = (value: string) => {
	const date = new Date(value);
	return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};
export const normalizeQuestion = (question: Question): Question => ({
	...question,
	options: Array.isArray(question.options) ? question.options : [],
	answer: Number.isInteger(question.answer) ? question.answer : 0,
	area: question.area || 'Otro',
	synthetic: Boolean(question.synthetic)
});
