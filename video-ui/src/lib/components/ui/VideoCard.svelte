<script lang="ts">
    import { resolve } from "$app/paths";

    let { video } = $props();

    const options: Intl.DateTimeFormatOptions = {
        // weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return "Invalid Date";
        // return date.toLocaleDateString("en-IN", options);
        return new Intl.DateTimeFormat("en-IN", options).format(date);
    };
</script>

<a
    href={resolve(`/video/${video.id}`)}
    class="block w-90 border border-gray-300 rounded-sm shadow-md overflow-hidden bg-white
    transition hover:shadow-xl hover:-translate-y-1 cursor-pointer"
>
    <!-- Video Thumbnail -->
    <div class="h-52 w-full overflow-hidden">
        <img 
            src={video.thumbnail_key}
            alt="thumbnail"
            class="w-full h-full object-cover"
        />
    </div>

    <!-- Content -->
    <div class="p-4 flex flex-col gap-2">
        <!-- Title -->
        <h2 class="text-lg font-sans font-semibold leading-snug text-black tracking-wide">
            {video.title}
        </h2>

        <!-- Category -->
        <p class="text-sm text-gray-600 font-medium">
            {video.category.name}
        </p>

        <!-- Meta -->
        <div class="flex justify-between text-sm text-gray-500 pt-2">
            <span>Uploaded: {formatDate(video.published_at)}</span>
            <span>{video.view_count} views</span>
        </div>
        
    </div>
</a>