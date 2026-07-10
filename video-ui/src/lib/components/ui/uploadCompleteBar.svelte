<script lang="ts">
    
</script>

<div class="rounded-xl border border-emerald-100 bg-emerald-50/40 px-4 py-3">
    <!-- Top Row -->
    <div class="flex items-center justify-between gap-3">
        <!-- Left -->
            <div class="flex min-w-0 items-center gap-2">
            <!-- Icon -->
            <div
                class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-500"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="white"
                    class="size-3.5"
                >
                    <path
                        fill-rule="evenodd"
                        d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z"
                        clip-rule="evenodd"
                    />
                </svg>
            </div>

            <!-- Text -->
            <div class="min-w-0">
                <div class="flex items-center gap-2">
                    <p class="text-sm font-semibold text-emerald-700">
                        Upload Complete
                    </p>

                    <span class="text-xs text-gray-400">
                        100%
                    </span>
                </div>

                <p class="truncate text-xs text-gray-500">
                    <!-- {workflow.workflowProgress.selectedVideoFile?.name} -->
                </p>
            </div>
        </div>

        <!-- Status Pill -->
        <div
            class="rounded-full bg-white px-2 py-1 text-[11px] font-medium text-emerald-600 ring-1 ring-emerald-100"
        >
            Ready
        </div>

    </div>

    <!-- Progress -->
    <div class="mt-3">
        <div class="relative h-1.5 overflow-hidden rounded-full bg-emerald-100">

            <!-- fill -->
            <div
                class="absolute inset-0 rounded-full bg-linear-to-r from-emerald-400 via-green-500 to-teal-400"
            ></div>

            <!-- shine -->
            <div
                class="absolute inset-0 bg-[linear-gradient(110deg,transparent,rgba(255,255,255,0.35),transparent)]
                bg-size-[200%_100%] animate-[shimmer_3s_linear_infinite]"
            ></div>
        </div>
    </div>
    
</div>