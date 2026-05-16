<script lang="ts">
	import './layout.css';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href="https://bonsanbec.dev/favicon.svg" /></svelte:head>
{@render children()}
