<script lang="ts">
	import type { ForestTree } from './model';

	let { trees }: { trees: ForestTree[] } = $props();
</script>

<section class="mt-4 rounded-lg bg-white p-4 shadow-sm">
	<h2 class="mb-3 text-lg font-bold">Bosque de conocimiento ({trees.length})</h2>
	{#if trees.length === 0}
		<p class="text-sm text-gray-700">Sin árboles registrados.</p>
	{:else}
		<div class="grid gap-3 md:grid-cols-2">
			{#each trees as tree (tree.id)}
				<div class="rounded border border-gray-200 p-3 text-sm">
					<h3 class="font-bold">{tree.name}</h3>
					{#if tree.description}<p class="mt-1 text-gray-700">{tree.description}</p>{/if}
					<div class="mt-3 space-y-2">
						{#each Object.values(tree.nodes ?? {}) as node (node.id)}
							<div>
								<div class="font-bold">{node.name}</div>
								{#each Object.values(node.leaves ?? {}) as leaf (leaf.id)}
									<div class="ml-3 text-gray-700">
										{leaf.name}: {leaf.question_count ?? 0} preguntas, {leaf.materials?.length ?? 0} materiales
									</div>
								{/each}
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</section>
