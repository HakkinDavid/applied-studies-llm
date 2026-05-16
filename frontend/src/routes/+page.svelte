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
	let loadingAll = $state(false);
	let loadingReferences = $state(false);
	let uploading = $state(false);
	let error = $state('');
	let notice = $state('');

	const selectedMaterial = $derived(
		materials.find((material) => material.id === selectedMaterialId) ?? null
	);
	const forestTrees = $derived(Object.values(forest?.trees ?? {}));

	onMount(() => {
		const configuredBase = import.meta.env.VITE_API_BASE_URL;
		apiBase =
			typeof configuredBase === 'string' && configuredBase
				? configuredBase.replace(/\/$/, '')
				: 'http://localhost:8000'; // yo cuando el loco es host o como
		void refreshAll();
	});

	const url = (path: string) =>
		`${(typeof apiBase === 'string' ? apiBase : '').replace(/\/$/, '')}${path}`;

	async function api<T>(path: string, init?: RequestInit) {
		const response = await fetch(url(path), init);
		const text = await response.text();
		let body: unknown;
		try {
			body = text ? JSON.parse(text) : null;
		} catch {
			body = text || null;
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
			api<KnowledgeForestResponse>('/api/knowledge-forest').then((data) => (forest = data.forest))
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
				)
			]);
		} catch (problem) {
			fail(problem);
		}
		uploading = false;
	}

    async function deleteMaterial(id: string) {
		if (!confirm('¿En serio?')) return;
		try {
			await api(`/api/materials/${id}`, { method: 'DELETE' });
            refreshAll();
			notice = 'Material borrado.';
		} catch (problem) {
			fail(problem);
		}
	}

    // la neta la neta el ts está bien chafa pero pues más chafa es volverse loquito buscando quién es [object Object] (no soy yo)
</script>

<svelte:head><title>Applied Studies LLM</title></svelte:head>

<main class="min-h-screen bg-gray-100 px-4 py-5 text-gray-900">
	<div class="mx-auto max-w-6xl">
		<header
			class="mb-4 flex flex-col gap-3 border-b border-gray-300 pb-4 md:flex-row md:items-center md:justify-between"
		>
			<div>
				<p class="text-xl text-gray-600">Applied Studies LLM</p>
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
			loading={loadingAll}
			{uploading}
			setApiBase={(value) => (apiBase = value)}
			refresh={refreshAll}
			upload={uploadMaterial}
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
            {deleteMaterial}
		/>
		<!--jugaremos en el bosque mientras el mtro. ortega no está, porque si de pronto aparece los comentarios nos leerá-->
		<ForestPanel trees={forestTrees} />
        <!--profe profe esta ahi??-->
	</div>

    <footer class="mt-4 text-center text-xs text-gray-500">
        Inspirado por mi proyecto:
        <a
            href="https://hakkindavid.github.io/CETYS/egel_prueba.html"
            class="text-blue-600 hover:underline"
        >
            hakkindavid.github.io/CETYS/egel_prueba.html
        </a>
    </footer>
</main>
