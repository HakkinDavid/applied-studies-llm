<script lang="ts">
	let {
		onclick,
        children,
        disabled = false,
        classes,
        submit = false
	}: {
		onclick?: () => void;
        disabled?: boolean;
        children: () => ReturnType<import("svelte").Snippet>;
        classes?: string;
        submit?: boolean;
	} = $props();
</script>

<button
	type="{submit ? 'submit' : 'button'}"
	class="cursor-pointer rounded border px-3 py-2 text-sm {classes ?? "border-gray-400 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"}"
	onclick={onclick}
	disabled={disabled}
>
	{@render children()}
</button>
