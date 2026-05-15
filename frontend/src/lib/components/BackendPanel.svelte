<script lang="ts">
	import type { HealthResponse, UploadInput } from './model';

	let {
		apiBase,
		health,
		questionsCount,
		compatibleJsCount,
		loading,
		uploading,
		setApiBase,
		refresh,
		upload,
		clearQuestions,
		clearForest
	}: {
		apiBase: string;
		health: HealthResponse | null;
		questionsCount: number;
		compatibleJsCount: number | null;
		loading: boolean;
		uploading: boolean;
		setApiBase: (value: string) => void;
		refresh: () => void | Promise<void>;
		upload: (input: UploadInput) => void | Promise<void>;
		clearQuestions: () => void | Promise<void>;
		clearForest: () => void | Promise<void>;
	} = $props();

	let file = $state<File | null>(null);
	let treeHint = $state('');
	let numQuestions = $state(15);
</script>

<section class="mb-4 rounded-lg bg-white p-4 shadow-sm">
	<div class="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
		<div>
			<h2 class="mb-3 text-lg font-bold">Backend</h2>
			<label class="mb-2 block text-sm font-bold" for="apiBase">API</label>
			<div class="flex gap-2">
				<input
					id="apiBase"
					class="w-full rounded border-gray-300 text-sm"
					type="text"
					placeholder="http://localhost:8000"
					value={apiBase}
					oninput={(event) => setApiBase(event.currentTarget.value)}
				/>
				<button
					type="button"
					class="rounded border border-gray-400 px-3 py-2 text-sm hover:bg-gray-100"
					onclick={() => void refresh()}
					disabled={loading}
				>
					Probar
				</button>
			</div>

			<div class="mt-3 grid gap-2 text-sm sm:grid-cols-2">
				<div>
					<strong>Estado:</strong>
					<span class={health?.status === 'ok' ? 'text-green-700' : 'text-red-700'}>
						{health?.status ?? 'sin conexion'}
					</span>
				</div>
				<div><strong>IA:</strong> {health?.ai_configured ? 'configurada' : 'sin configurar'}</div>
				<div><strong>Modelo:</strong> {health?.model || '-'}</div>
				<div><strong>Base URL:</strong> {health?.base_url || '-'}</div>
				<div><strong>Preguntas JSON:</strong> {questionsCount}</div>
				<div><strong>JS compatible:</strong> {compatibleJsCount ?? '-'}</div>
			</div>
		</div>

		<form
			class="border-t border-gray-200 pt-4 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-4"
			onsubmit={(event) => {
				event.preventDefault();
				void upload({ file, treeHint, numQuestions });
			}}
		>
			<h2 class="mb-3 text-lg font-bold">Material</h2>
			<div class="grid gap-3 sm:grid-cols-[1fr_140px]">
				<label class="block text-sm font-bold">
					Archivo
					<input
						class="mt-1 block w-full rounded border-gray-300 text-sm"
						type="file"
						accept=".pdf,.txt,.md,.docx"
						onchange={(event) => (file = event.currentTarget.files?.[0] ?? null)}
					/>
				</label>
				<label class="block text-sm font-bold">
					Preguntas
					<input
						class="mt-1 block w-full rounded border-gray-300 text-sm"
						type="number"
						min="1"
						max="40"
						bind:value={numQuestions}
					/>
				</label>
			</div>
			<label class="mt-3 block text-sm font-bold">
				Pista de arbol
				<input
					class="mt-1 block w-full rounded border-gray-300 text-sm"
					type="text"
					placeholder="ICC, matematicas, derecho..."
					bind:value={treeHint}
				/>
			</label>
			<div class="mt-3 flex flex-wrap gap-2">
				<button
					type="submit"
					class="rounded border border-gray-700 bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800"
					disabled={uploading}
				>
					{uploading ? 'Procesando...' : 'Subir y generar'}
				</button>
				<button
					type="button"
					class="rounded border border-red-300 px-4 py-2 text-sm text-red-700 hover:bg-red-50"
					onclick={() => void clearQuestions()}
				>
					Borrar banco
				</button>
				<button
					type="button"
					class="rounded border border-red-300 px-4 py-2 text-sm text-red-700 hover:bg-red-50"
					onclick={() => void clearForest()}
				>
					Borrar bosque
				</button>
			</div>
		</form>
	</div>
</section>
