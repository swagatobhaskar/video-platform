<script lang="ts">
    // pole the progress percent API endpoint. Need video_id or task_id
</script>

<div class="rounded-xl border border-slate-100 bg-slate-50/40 px-4 py-3 min-h-16">
    <!-- Top Row -->
    <div class="flex items-center justify-between gap-3">
        <!-- Left -->
            <div class="flex min-w-0 items-center gap-2">
            <!-- Loading GIF -->
            <div class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full">
                <img src="/loading.gif" alt="Loading" />
            </div>

            <!-- Text -->
            <div class="min-w-0">
                <div class="flex items-center gap-2">
                    <p class="text-sm font-semibold text-slate-700">
                        Processing Video
                    </p>

                    <span class="text-xs text-gray-600">
                        60%
                    </span>
                    
                    <!-- Status Pill -->
                    <!-- <div class="rounded-full bg-white px-2 py-1 text-[11px] font-medium text-emerald-600 ring-1 ring-slate-100">
                        60%
                    </div> -->
                </div>
            </div>
        </div>
    </div>    
</div>