<script lang="ts">
	import { onMount } from 'svelte';
	import BackendPanel from '$lib/components/BackendPanel.svelte';
	import ForestPanel from '$lib/components/ForestPanel.svelte';
	import MaterialsPanel from '$lib/components/MaterialsPanel.svelte';
	import QuizPanel from '$lib/components/QuizPanel.svelte';
	import {
		normalizeQuestion,
		type HealthResponse,
		type KnowledgeForest,
		type KnowledgeForestResponse,
		type Material,
		type MaterialListResponse,
		type MaterialReference,
		type MaterialReferencesResponse,
		type Question,
		type QuestionBankResponse,
		type UploadInput
	} from '$lib/components/model';

	let apiBase = $state('');
	let health = $state<HealthResponse | null>(null);
	let materials = $state<Material[]>([]);
	let selectedMaterialId = $state('');
	let references = $state<MaterialReference[]>([]);
	let questions = $state<Question[]>([]);
	let forest = $state<KnowledgeForest | null>(null);
	let compatibleJsCount = $state<number | null>(null);
	let loadingAll = $state(false);
	let loadingReferences = $state(false);
	let uploading = $state(false);
	let error = $state('');
	let notice = $state('');

	const selectedMaterial = $derived(
		materials.find((material) => material.id === selectedMaterialId) ?? null
	);

	onMount(() => {
		apiBase =
			import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');
		void refreshAll();
	});

	const url = (path: string) => `${apiBase.replace(/\/$/, '')}${path}`;

	async function api<T>(path: string, init?: RequestInit) {
		const response = await fetch(url(path), init);
		const text = await response.text();
		let body: unknown = text;
		try {
			body = text ? JSON.parse(text) : null;
		} catch {
		}
		if (!response.ok) {
			const detail =
				typeof body === 'object' && body && 'detail' in body
					? (body as { detail: unknown }).detail
					: body;
			throw new Error(typeof detail === 'string' ? detail : `Error HTTP ${response.status}`);
		}
		return body as T;
	}

	function fail(problem: unknown) {
		error = problem instanceof Error ? problem.message : String(problem);
	}

	async function refreshAll() {
		loadingAll = true;
		error = '';
		notice = '';
		const jobs = await Promise.allSettled([
			api<HealthResponse>('/api/health').then((data) => (health = data)),
			api<QuestionBankResponse>('/api/question-bank').then(
				(data) => (questions = data.questions.map(normalizeQuestion))
			),
			refreshMaterials(),
			api<KnowledgeForestResponse>('/api/knowledge-forest').then((data) => (forest = data.forest)),
			refreshCompatibleJs()
		]);
		const rejected = jobs.find((job) => job.status === 'rejected');
		if (rejected?.status === 'rejected') fail(rejected.reason);
		loadingAll = false;
	}

	async function refreshMaterials() {
		const data = await api<MaterialListResponse>('/api/materials');
		materials = data.materials;
		selectedMaterialId = materials.some((material) => material.id === selectedMaterialId)
			? selectedMaterialId
			: (materials[0]?.id ?? '');
		references = selectedMaterialId
			? (await api<MaterialReferencesResponse>(`/api/materials/${selectedMaterialId}/references`))
					.references
			: [];
	}

	async function refreshCompatibleJs() {
		const response = await fetch(url('/egel/banco_preguntas.js'));
		if (!response.ok)
			throw new Error(`No se pudo cargar /egel/banco_preguntas.js (${response.status})`);
		compatibleJsCount = JSON.parse(
			(await response.text())
				.trim()
				.replace(/^window\.questions\s*=\s*/, '')
				.replace(/;\s*$/, '')
		).length;
	}

	async function loadReferences(id: string) {
		loadingReferences = true;
		selectedMaterialId = id;
		try {
			references = (await api<MaterialReferencesResponse>(`/api/materials/${id}/references`))
				.references;
		} catch (problem) {
			references = [];
			fail(problem);
		}
		loadingReferences = false;
	}

	async function uploadMaterial({ file, treeHint, numQuestions }: UploadInput) {
		if (!file) {
			fail('Selecciona un archivo.');
			return;
		}
		uploading = true;
		error = '';
		notice = '';

		const form = new FormData();
		form.append('file', file);
		form.append('num_questions', String(numQuestions));
		if (treeHint.trim()) form.append('tree_hint', treeHint.trim());

		try {
			const material = await api<Material>('/api/materials/upload', { method: 'POST', body: form });
			notice = `${material.original_filename}: ${material.generated_questions} preguntas disponibles.`;
			selectedMaterialId = material.id;
			await Promise.all([
				api<QuestionBankResponse>('/api/question-bank').then(
					(data) => (questions = data.questions.map(normalizeQuestion))
				),
				refreshMaterials(),
				api<KnowledgeForestResponse>('/api/knowledge-forest').then(
					(data) => (forest = data.forest)
				),
				refreshCompatibleJs()
			]);
		} catch (problem) {
			fail(problem);
		}
		uploading = false;
	}

	async function clearQuestionBank() {
		if (!confirm('Borrar el banco de preguntas generado?')) return;
		try {
			await api('/api/question-bank', { method: 'DELETE' });
			questions = [];
			await refreshCompatibleJs();
			notice = 'Banco de preguntas borrado.';
		} catch (problem) {
			fail(problem);
		}
	}

	async function clearKnowledgeForest() {
		if (!confirm('Borrar el bosque de conocimiento?')) return;
		try {
			await api('/api/knowledge-forest', { method: 'DELETE' });
			forest = { trees: {} };
			notice = 'Bosque de conocimiento borrado.';
		} catch (problem) {
			fail(problem);
		}
	}
</script>

<svelte:head><title>Applied Studies LLM</title></svelte:head>

<main class="min-h-screen bg-gray-100 px-4 py-5 text-gray-900">
	<div class="mx-auto max-w-6xl">
		<header
			class="mb-4 flex flex-col gap-3 border-b border-gray-300 pb-4 md:flex-row md:items-center md:justify-between"
		>
			<div>
				<p class="text-sm text-gray-600">Applied Studies LLM</p>
			</div>
			<button
				type="button"
				class="rounded border border-gray-400 bg-white px-3 py-2 text-sm hover:bg-gray-100"
				onclick={refreshAll}
				disabled={loadingAll}
			>
				{loadingAll ? 'Actualizando...' : 'Actualizar'}
			</button>
		</header>

		{#if error}<div
				class="mb-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
			>
				{error}
			</div>{/if}
		{#if notice}<div
				class="mb-4 rounded border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800"
			>
				{notice}
			</div>{/if}

		<BackendPanel
			{apiBase}
			{health}
			questionsCount={questions.length}
			{compatibleJsCount}
			loading={loadingAll}
			{uploading}
			setApiBase={(value) => (apiBase = value)}
			refresh={refreshAll}
			upload={uploadMaterial}
			clearQuestions={clearQuestionBank}
			clearForest={clearKnowledgeForest}
		/>

		<QuizPanel {questions} />
        <!--yo cuando me materializo-->
		<MaterialsPanel
			{materials}
			{selectedMaterial}
			{selectedMaterialId}
			{references}
			{loadingReferences}
			{loadReferences}
		/>
		
	</div>
</main>
