<script lang="ts">
	import { onMount } from 'svelte';

	let apiBase = $state('');

	onMount(() => {
		apiBase =
			import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '');
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
</script>

<svelte:head><title>Applied Studies LLM</title></svelte:head>
