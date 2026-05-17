<script lang="ts">
	import { onMount } from 'svelte';
	import Button from './Button.svelte';
	import type {
		Material,
		ConversationSummary,
		ConversationMessage,
		ConversationResponse
	} from './model';

	let {
		selectedMaterial,
		selectedMaterialId,
		loadReferences,
		apiBaseUrl = ''
	}: {
		materials: Material[];
		selectedMaterial: Material | null;
		selectedMaterialId: string;
		loadReferences: (materialId: string) => void | Promise<void>;
		apiBaseUrl?: string;
	} = $props();

	const STORAGE_KEY = 'asllm-conversations-cache';
	const chatbot_name = 'Kuchumá (Gran Sabio)';
	const user_name = 'Tú';

	let conversations = $state<ConversationSummary[]>([]);
	let selectedConversationId = $state('');
	let messages = $state<ConversationMessage[]>([]);
	let message = $state('');
	let loadingConversation = $state(false);
	let processingMessage = $state(false);

	function loadConversationCache() {
		try {
			conversations = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
		} catch {
			conversations = [];
		}
	}

	function resetConversationSession(clearMessage = true) {
		selectedConversationId = '';
		messages = [];
		processingMessage = false;
		loadingConversation = false;

		if (clearMessage) {
			message = '';
		}
	}

	async function createConversation(question: string) {
		if (!selectedMaterialId || !question.trim()) {
			return;
		}

		processingMessage = true;

		try {
			const response = await fetch(`${apiBaseUrl}/api/materials/${selectedMaterialId}/ask`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					question: question.trim(),
					top_k: 5
				})
			});

			if (!response.ok) {
				throw new Error('No se pudo crear la conversación.');
			}

			const data = (await response.json()) as ConversationResponse;

			const conversation: ConversationSummary = {
				conversation_id: data.conversation_id,
				title: data.question,
				material_id: data.material_id,
				material_name: data.material_name
			};

			if (!conversations.some((item) => item.conversation_id === conversation.conversation_id)) {
				conversations = [conversation, ...conversations];
				localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
			}

			selectedConversationId = data.conversation_id;

			messages = [
				...messages.filter((item) => item.role === 'user'),
				{ role: 'assistant', content: data.answer }
			];
		} finally {
			processingMessage = false;
		}
	}

	async function loadConversation(conversationId: string) {
		selectedConversationId = conversationId;
		processingMessage = false;
		loadingConversation = true;

		try {
			const response = await fetch(`${apiBaseUrl}/api/conversations/${conversationId}`);

			if (!response.ok) {
				throw new Error('No se pudo cargar la conversación.');
			}

			const data = await response.json();

			if (data.material_id) {
				await loadReferences(data.material_id);
			}

			messages = (data.messages ?? []).flatMap((item: any) => {
				const mapped: ConversationMessage[] = [];

				if (item.question) {
					mapped.push({
						role: 'user',
						content: item.question
					});
				}

				if (item.answer) {
					mapped.push({
						role: 'assistant',
						content: item.answer
					});
				}

				if (item.role && item.content) {
					mapped.push({
						role: item.role === 'assistant' ? 'assistant' : 'user',
						content: item.content
					});
				}

				return mapped;
			});
		} finally {
			loadingConversation = false;
		}
	}

	async function sendMessage() {
		if (!message.trim()) {
			return;
		}

		const question = message.trim();

		if (!selectedConversationId) {
			messages = [
				{
					role: 'user',
					content: question
				}
			];

			processingMessage = true;
			message = '';

			await createConversation(question);
			return;
		}

		processingMessage = true;

		messages = [...messages, { role: 'user', content: question }];

		message = '';

		try {
			const response = await fetch(
				`${apiBaseUrl}/api/conversations/${selectedConversationId}/messages`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify({
						question,
						top_k: 5
					})
				}
			);

			if (!response.ok) {
				throw new Error('No se pudo enviar el mensaje.');
			}

			const data = (await response.json()) as ConversationResponse;

			messages = [...messages, { role: 'assistant', content: data.answer }];
		} finally {
			processingMessage = false;
		}
	}

	onMount(() => {
		loadConversationCache();
		resetConversationSession();
	});

	let previousMaterialId = $state('');

	$effect(() => {
		if (!selectedMaterialId || selectedMaterialId === previousMaterialId) {
			return;
		}

		previousMaterialId = selectedMaterialId;

		if (!loadingConversation) {
			resetConversationSession();
		}
	});
</script>

<div class="mt-4 grid gap-4 lg:grid-cols-[320px_1fr]">
	<section class="rounded-lg bg-white p-4 shadow-sm">
		<div class="mb-4">
			<div class="flex items-center justify-between gap-2">
				<h2 class="text-lg font-bold">
					Conversaciones ({conversations.length})
				</h2>

				<Button
					classes="border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
					onclick={() => resetConversationSession()}
				>
					Nuevo chat
				</Button>
			</div>

			<p class="mt-2 text-sm text-gray-700">
				Selecciona un material y envía un mensaje para iniciar una conversación.
			</p>
		</div>

		{#if conversations.length === 0}
			<p class="text-sm text-gray-700">Sin conversaciones registradas.</p>
		{:else}
			<div class="max-h-[600px] space-y-2 overflow-y-auto">
				{#each conversations as conversation (conversation.conversation_id)}
					<Button
						classes={`block w-full p-3 text-left hover:bg-gray-50 ${
							conversation.conversation_id === selectedConversationId
								? 'border-gray-900'
								: 'border-gray-200'
						}`}
						onclick={async () => {
							messages = [];
							await loadConversation(conversation.conversation_id);
						}}
					>
						<div class="font-bold">{conversation.title || 'Conversación'}</div>

						<div class="mt-1 text-xs break-all text-gray-600">
							{conversation.conversation_id}
						</div>
					</Button>
				{/each}
			</div>
		{/if}
	</section>

	<section class="flex h-[780px] flex-col overflow-hidden rounded-lg bg-white p-4 shadow-sm">
		<div class="mb-4 border-b border-gray-200 pb-3">
			<h2 class="text-lg font-bold">Chat</h2>

			<div class="mt-2 text-sm break-all text-gray-700">
				<div class="mb-3 flex items-center gap-2">
					{#if selectedMaterial}
						<div
							class="inline-flex items-center gap-2 rounded-full border border-gray-300 bg-gray-100 px-3 py-1 text-xs font-medium text-gray-800"
						>
							<!--svg generado con IA profe, tenga piedad, yo no le muevo bien al diseño-->
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								class="h-4 w-4"
							>
								<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
								<polyline points="14 2 14 8 20 8" />
								<line x1="16" y1="13" x2="8" y2="13" />
								<line x1="16" y1="17" x2="8" y2="17" />
								<polyline points="10 9 9 9 8 9" />
							</svg>

							<span class="max-w-[260px] truncate">
								{selectedMaterial.original_filename}
							</span>
						</div>
					{:else}
						<div class="text-sm text-gray-600">Sin material seleccionado</div>
					{/if}
				</div>
				ID conversación:
				<strong>
					{selectedConversationId || 'Sin conversación seleccionada'}
				</strong>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto pr-2">
			{#if loadingConversation}
				<p class="text-sm text-gray-700">Cargando conversación...</p>
			{:else if messages.length === 0}
				<p class="text-sm text-gray-700">Sin mensajes.</p>
			{:else}
				<div class="space-y-4">
					{#each messages as item, index}
						<div
							class={`rounded-lg p-3 text-sm ${
								item.role === 'user' ? 'bg-gray-100' : 'border border-gray-200'
							}`}
						>
							<div class="mb-2 flex items-center gap-2">
								<img
									src={item.role === 'user' ? 'user.png' : 'kuchuma.svg'}
									alt={item.role === 'user' ? user_name : chatbot_name}
									class="h-8 w-8 object-cover"
								/>

								<div class="font-bold">
									{item.role === 'user' ? user_name : chatbot_name}
								</div>
							</div>

							<p class="break-words whitespace-pre-wrap">
								{item.content}
							</p>
						</div>
					{/each}
					{#if processingMessage}
						<div class="rounded-lg border border-gray-200 p-3 text-sm">
							<div class="mb-2 flex items-center gap-2">
								<img
									src="kuchuma.svg"
									alt={chatbot_name}
									class="h-8 w-8 object-cover"
								/>

								<div class="font-bold">{chatbot_name}</div>
							</div>

                            <!--animación generada con IA profe, tenga piedad, yo no le muevo bien al diseño-->
							<div class="flex items-center gap-2 text-gray-600">
								<div class="h-2 w-2 animate-pulse rounded-full bg-gray-500"></div>
								<div class="h-2 w-2 animate-pulse rounded-full bg-gray-500"></div>
								<div class="h-2 w-2 animate-pulse rounded-full bg-gray-500"></div>
								<span>Pensando en las alturas...</span>
							</div>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<div class="mt-4 border-t border-gray-200 pt-4">
			<div class="flex gap-2">
				<input
					bind:value={message}
					type="text"
					placeholder="Escribe un mensaje..."
					class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
					onkeydown={(event) => {
						if (event.key === 'Enter') {
							void sendMessage();
						}
					}}
				/>

				<Button classes="border-gray-900 px-4 py-2 text-sm" onclick={() => void sendMessage()}>
					Enviar
				</Button>
			</div>
		</div>
	</section>
</div>
