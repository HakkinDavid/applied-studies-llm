<script lang="ts">
	import { onMount } from 'svelte';
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
		type QuestionBankResponse
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
	let error = $state('');
	let notice = $state('');

	onMount(() => {
		apiBase = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');
		void refreshAll();
	});

	const url = (path: string) => `${apiBase.replace(/\/$/, '')}${path}`;

	async function api<T>(path: string, init?: RequestInit) {
		const response = await fetch(url(path), init);
		const text = await response.text();
		let body: unknown = text;
		try {
			body = text ? JSON.parse(text) : null;
		} catch {}
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
	</div>
</main>
