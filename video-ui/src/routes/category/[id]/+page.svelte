<script lang="ts">
    let { data } = $props();
</script>

<main>
    <img 
        src={data.category.r2_category_image_key}
        alt={data.category.name}
        height="600"
        width="600"
        class="aspect-square w-1/5 object-cover transition-transform duration-300 group-hover:scale-105"
    />
    <p>Category name: {data.category.name}</p>
</main>