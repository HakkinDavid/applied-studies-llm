<script lang="ts">
	import { formatBytes, formatDate, pageLabel } from './model';
	import type { Material, MaterialReference } from './model';

	let {
		materials,
		selectedMaterial,
		selectedMaterialId,
		references,
		loadingReferences,
		loadReferences
	}: {
		materials: Material[];
		selectedMaterial: Material | null;
		selectedMaterialId: string;
		references: MaterialReference[];
		loadingReferences: boolean;
		loadReferences: (id: string) => void | Promise<void>;
	} = $props();
</script>

<div class="grid gap-4 lg:grid-cols-2">
	<section class="rounded-lg bg-white p-4 shadow-sm">
		<h2 class="mb-3 text-lg font-bold">Materiales ({materials.length})</h2>
		{#if materials.length === 0}
			<p class="text-sm text-gray-700">Sin materiales registrados.</p>
		{:else}
			<div class="space-y-3">
				{#each materials as material (material.id)}
					<button
						type="button"
						class={`block w-full rounded border p-3 text-left text-sm hover:bg-gray-50 ${
							material.id === selectedMaterialId ? 'border-gray-900' : 'border-gray-200'
						}`}
						onclick={() => void loadReferences(material.id)}
					>
						<div class="flex flex-wrap items-center justify-between gap-2">
							<strong>{material.original_filename}</strong>
							<span>{material.generated_questions} preguntas</span>
						</div>
						<div class="mt-1 text-gray-600">
							{formatBytes(material.size_bytes)} : {material.reference_count} referencias del {formatDate(
								material.uploaded_at
							)}
						</div>
						{#if material.knowledge_path}<div class="mt-1 text-gray-700">
								{material.knowledge_path}
							</div>{/if}
						{#if material.duplicate}<div class="mt-1 text-yellow-700">
								Duplicado SHA-256 reutilizado.
							</div>{/if}
					</button>
				{/each}
			</div>
		{/if}
	</section>

	<section class="rounded-lg bg-white p-4 shadow-sm">
		<h2 class="mb-3 text-lg font-bold">Referencias</h2>
		{#if selectedMaterial}<p class="mb-3 text-sm text-gray-700">
				{selectedMaterial.original_filename}
			</p>{/if}
		{#if loadingReferences}
			<p class="text-sm text-gray-700">Cargando referencias...</p>
		{:else if references.length === 0}
			<p class="text-sm text-gray-700">Sin referencias para mostrar.</p>
		{:else}
			<div class="max-h-[420px] space-y-3 overflow-auto pr-1">
				{#each references as reference (reference.ref_id)}
					<div class="border-b border-gray-200 pb-3 text-sm">
						<div class="mb-1 font-bold">{reference.ref_id} de {pageLabel(reference.page)}</div>
						<p>{reference.excerpt}</p>
					</div>
				{/each}
			</div>
		{/if}
	</section>
</div>
