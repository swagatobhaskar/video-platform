<script lang="ts">
    let {
        id,
        label,
        help,
        placeholder = "Add a keyword...",
        keywords = $bindable<string[]>([]),
    }: {id: string, label: string, help?: string, placeholder?: string, keywords: string[];} = $props();

    let entry = $state('');

    function add() {
        const value = entry.trim();
        if (!value) return;

        const exists = keywords.some(k => k.toLowerCase() === value.toLowerCase());
        if (!exists) keywords.push(value);
        entry = '';
    }

    function remove(index: number) {
        keywords.splice(index, 1);
    }
</script>

<div class="space-y-3">
    <div>
        <label for={id} class="block text-sm font-semibold tracking-wide text-gray-700">{label}</label>
        {#if help}<p id="{id}-help" class="text-sm text-gray-600">{help}</p>{/if}
    </div>

    <div class="flex gap-3">
        <input
            {id}
            type="text"
            bind:value={entry}
            {placeholder}
            aria-describedby={help ? `${id}-help` : undefined}
            onkeydown={(e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    add();
                }
            }}
            class="..."
        />
        <button type="button" onclick={add} disabled={!entry.trim()} class="...">Add</button>
    </div>

    <div class="...">
        {#if keywords.length === 0}
            <div class="flex items-center text-sm text-gray-400">No keywords added yet</div>
        {:else}
            {#each keywords as keyword, i (keyword)}
                <div class="...">
                    <span>{keyword}</span>
                    <button type="button" onclick={() => remove(i)} aria-label="Remove {keyword}">&times;</button>
                </div>
            {/each}
        {/if}
    </div>
</div>
