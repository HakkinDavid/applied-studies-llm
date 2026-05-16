<script lang="ts">
	import { onDestroy } from 'svelte';
	import { LEVELS, areaOf, formatTime, pageLabel, subareaOf } from './model';
	import type { Question, ResultRow } from './model';

	let { questions }: { questions: Question[] } = $props();

	let levelName = $state('Intermedio');
	let selectedAreas = $state<string[]>([]);
	let includeSynthetic = $state(true);
	let session = $state<Question[]>([]);
	let answers = $state<Record<number, number>>({});
	let index = $state(0);
	let timeLeft = $state(0);
	let quizState = $state<'idle' | 'running' | 'finished'>('idle');
	let rows = $state<ResultRow[]>([]);
	let error = $state('');
	let knownAreaKey = '';
	let timer: ReturnType<typeof setInterval> | null = null;

	const level = $derived(LEVELS.find((item) => item.name === levelName) ?? LEVELS[2]);
	const current = $derived(session[index]);
	const answered = $derived(Object.keys(answers).length);
	const score = $derived(rows.filter((row) => row.isCorrect).length);
	const areaOptions = $derived(Array.from(new Set(questions.map(areaOf))));
	const areaStats = $derived(stats('area'));
	const subareaStats = $derived(stats('subarea'));

	$effect(() => {
		const nextAreaKey = areaOptions.join('\u0000');

		if (nextAreaKey !== knownAreaKey) {
			const previousAreas = knownAreaKey ? knownAreaKey.split('\u0000') : [];
			const keptAreas = selectedAreas.filter((area) => areaOptions.includes(area));
			const newAreas = knownAreaKey
				? areaOptions.filter((area) => !previousAreas.includes(area))
				: areaOptions;

			selectedAreas = [...keptAreas, ...newAreas];
			knownAreaKey = nextAreaKey;
		}

		if (questions.length === 0 && quizState !== 'idle') reset();
	});

	onDestroy(stopTimer);

	function reset() {
		stopTimer();
		session = [];
		answers = {};
		rows = [];
		index = 0;
		timeLeft = 0;
		quizState = 'idle';
	}

	function start() {
		error = '';
		stopTimer();

		if (selectedAreas.length === 0) {
			error = 'Selecciona al menos un area para iniciar la simulación.';
			return;
		}

		const buckets: Record<string, Question[]> = Object.fromEntries(
			selectedAreas.map((area) => [area, [] as Question[]])
		);

		for (const question of questions) {
			const area = areaOf(question);
			if ((includeSynthetic || !question.synthetic) && area in buckets)
				buckets[area].push(question);
		}

		for (const area of selectedAreas) buckets[area] = shuffle(buckets[area] ?? []);

		const total = Math.min(
			level.questions,
			selectedAreas.reduce((sum, area) => sum + (buckets[area]?.length ?? 0), 0)
		);

        if (total < level.questions) {
			error = 'No hay suficientes preguntas para iniciar la simulación en este nivel (faltan ' + (level.questions - total) + ').';
            reset();
			return;
		}

		const perArea = Math.floor(total / selectedAreas.length);
		const picked: Question[] = [];

		selectedAreas.forEach((area, areaIndex) => {
			const quota = perArea + (areaIndex < total % selectedAreas.length ? 1 : 0);
			picked.push(...(buckets[area] ?? []).splice(0, quota));
		});

		picked.push(
			...shuffle(selectedAreas.flatMap((area) => buckets[area] ?? [])).slice(
				0,
				total - picked.length
			)
		);

		session = shuffle(
			picked.map((question) =>
				question.synthetic
					? shuffleOptions(question)
					: { ...question, options: [...question.options] }
			)
		);
		answers = {};
		rows = [];
		index = 0;
		timeLeft = level.time * 60;
		quizState = 'running';
		timer = setInterval(() => (timeLeft <= 1 ? finish() : (timeLeft -= 1)), 1000);
	}

	function finish() {
		stopTimer();
		rows = session.map((question, rowIndex) => {
			const selected = answers[rowIndex];
			return {
				index: rowIndex,
				question,
				userAnswer: selected === undefined ? 'Sin respuesta' : (question.options[selected] ?? '-'),
				correctAnswer: question.options[question.answer] ?? '-',
				isCorrect: selected === question.answer
			};
		});
		quizState = 'finished';
	}

	function stats(kind: 'area' | 'subarea') {
		return Object.values(
			rows.reduce(
				(all, row) => {
					const label = kind === 'area' ? areaOf(row.question) : subareaOf(row.question);
					if (label !== '-') {
						all[label] ??= { label, correct: 0, total: 0 };
						all[label].total += 1;
						if (row.isCorrect) all[label].correct += 1;
					}
					return all;
				},
				{} as Record<string, { label: string; correct: number; total: number }>
			)
		);
	}

	function stopTimer() {
		if (timer) clearInterval(timer);
		timer = null;
	}

	const shuffle = <T,>(items: T[]) => {
		const copy = [...items];
		for (let i = copy.length - 1; i > 0; i -= 1) {
			const j = Math.floor(Math.random() * (i + 1));
			[copy[i], copy[j]] = [copy[j], copy[i]];
		}
		return copy;
	};

	const shuffleOptions = (question: Question) => {
		const shuffled = shuffle(
			question.options.map((text, optionIndex) => ({ text, ok: optionIndex === question.answer }))
		);
		return {
			...question,
			options: shuffled.map((option) => option.text),
			answer: shuffled.findIndex((option) => option.ok)
		};
	};
</script>

<section class="mb-4 rounded-lg bg-white p-4 shadow-sm">
	<div id="levelSelector" class="grid gap-4 lg:grid-cols-[220px_1fr_auto] lg:items-end">
		<label class="block text-sm font-bold">
			Nivel de estudio
			<select class="mt-1 block w-full rounded border-gray-300 text-sm" bind:value={levelName}>
				{#each LEVELS as levelItem (levelItem.name)}
					<option value={levelItem.name} disabled={levelItem.questions > questions.length}>
						{levelItem.name} ({levelItem.questions} preguntas / {levelItem.time} min)
					</option>
				{/each}
			</select>
		</label>

		<div>
			<div class="mb-2 text-sm font-bold">Areas incluidas</div>
			<div class="flex flex-wrap gap-2">
				{#if areaOptions.length}
					{#each areaOptions as area (area)}
						<label class="rounded-full bg-gray-100 px-3 py-1 text-sm shadow-sm">
							<input
								class="mr-1 rounded border-gray-300"
								type="checkbox"
								checked={selectedAreas.includes(area)}
								onchange={() =>
									(selectedAreas = selectedAreas.includes(area)
										? selectedAreas.filter((item) => item !== area)
										: [...selectedAreas, area])}
							/>
							{area}
						</label>
					{/each}
				{:else}
					<span class="text-sm text-gray-600">Sin areas en el banco.</span>
				{/if}
			</div>
			<label class="mt-3 block text-sm">
				<input
					class="mr-1 rounded border-gray-300"
					type="checkbox"
					bind:checked={includeSynthetic}
				/>
				Incluir preguntas generadas por IA <!-- me voy dando cuenta que este vestigio de mi implementación para el egel no tiene motivo de ser aquí pero lo dejaremos por si luego hacemos listas curadas -->
			</label>
		</div>

		<button
			type="button"
			class="rounded border border-gray-700 bg-white px-5 py-2 text-sm font-bold hover:bg-gray-100"
			onclick={start}
		>
			Iniciar
		</button>
	</div>
</section>

{#if error}
	<div class="mb-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
		{error}
	</div>
{/if}

<div id="nav" class="mb-3 flex items-center justify-between gap-2">
	<button
		type="button"
		class="rounded border border-gray-400 bg-white px-4 py-2 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
		onclick={() => (index = Math.max(0, index - 1))}
		disabled={quizState !== 'running' || index === 0}
	>
		Anterior
	</button>
	<div class="text-sm text-gray-700">
		Tiempo: {formatTime(timeLeft)} con {answered}/{session.length} respondidas
	</div>
	<button
		type="button"
		class="rounded border border-gray-400 bg-white px-4 py-2 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
		onclick={() => (index < session.length - 1 ? (index += 1) : finish())}
		disabled={quizState !== 'running' || session.length === 0}
	>
		{index < session.length - 1 ? 'Siguiente' : 'Evaluar'}
	</button>
</div>

<section id="quiz" class="mb-4 rounded-lg bg-white p-4 shadow-sm">
	{#if quizState === 'running' && current}
		<div class="mb-3 flex items-start justify-between gap-3">
			<p class="font-bold">{index + 1} / {session.length}</p>
			<div class="flex items-center gap-2 text-sm text-gray-600">
				<span>{areaOf(current)}</span>
				<span
					class="group relative inline-flex h-6 w-6 items-center justify-center rounded-full border border-gray-300 bg-yellow-50 text-xs"
					title="Referencia"
				>
                <!-- aja un alt atributo pero pues es i-->
					<!-- svelte-ignore a11y_missing_attribute -->
					<img src="i.png">
					<span
						class="pointer-events-none absolute top-7 right-0 z-10 hidden w-80 rounded bg-gray-900 px-3 py-2 text-left text-xs leading-snug text-white shadow-lg group-hover:block"
					>
						<span class="block"
							><strong>Documento:</strong> {current.source_document_name ?? '-'}</span
						>
						<span class="block"
							><strong>Referencia:</strong>
							{current.source_ref_id ?? '-'} ({pageLabel(current.source_page)})</span
						>
						{#if current.knowledge_path}<span class="block"
								><strong>Ruta:</strong> {current.knowledge_path}</span
							>{/if}
						{#if current.source_excerpt}<span class="mt-1 block">{current.source_excerpt}</span
							>{/if}
					</span>
				</span>
			</div>
		</div>

		<p class="mb-4">{current.q}</p>
		<div class="space-y-2">
			{#each current.options as option, optionIndex (optionIndex)}
				<label class="block rounded border border-gray-200 px-3 py-2 text-sm hover:bg-gray-50">
					<input
						class="mr-2 border-gray-300"
						type="radio"
						name="current-question"
						value={optionIndex}
						checked={answers[index] === optionIndex}
						onchange={() => (answers = { ...answers, [index]: optionIndex })}
					/>
					{option}
				</label>
			{/each}
		</div>
	{:else if quizState === 'finished'}
		<h2 class="mb-2 text-lg font-bold">Resultado: {score}/{session.length}</h2>
		<div class="mb-3 flex flex-wrap gap-2 text-sm">
			{#each areaStats as stat (stat.label)}
				<span class="rounded bg-gray-100 px-2 py-1">{stat.label}: {stat.correct}/{stat.total}</span>
			{/each}
		</div>
		{#if subareaStats.length}
			<div class="mb-4 flex flex-wrap gap-2 text-sm">
				{#each subareaStats as stat (stat.label)}
					<span class="rounded bg-gray-100 px-2 py-1"
						>{stat.label}: {stat.correct}/{stat.total}</span
					>
				{/each}
			</div>
		{/if}
		<div class="overflow-x-auto">
			<table class="w-full border-collapse text-left text-sm">
				<thead>
					<tr class="border-b bg-gray-100">
						<th class="p-2">#</th>
						<th class="p-2">Área</th>
						<th class="p-2">Subárea</th>
						<th class="p-2">Origen</th>
						<th class="p-2">Pregunta</th>
						<th class="p-2">Respuesta</th>
						<th class="p-2">Correcta</th>
					</tr>
				</thead>
				<tbody>
					{#each rows as row (row.index)}
						<tr class={row.isCorrect ? 'border-b bg-green-50' : 'border-b bg-red-50'}>
							<td class="p-2">{row.index + 1}</td>
							<td class="p-2">{areaOf(row.question)}</td>
							<td class="p-2">{subareaOf(row.question)}</td>
							<td class="p-2">{row.question.synthetic ? 'IA' : 'Banco'}</td>
							<td class="p-2">{row.question.q}</td>
							<td class="p-2">{row.userAnswer}</td>
							<td class="p-2">{row.correctAnswer}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<p class="text-sm text-gray-700">Banco cargado: {questions.length} preguntas.</p>
	{/if}
</section>
