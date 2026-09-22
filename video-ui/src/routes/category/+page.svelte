<script lang="ts">
  let { data } = $props();
  import {resolve} from "$app/paths";
</script>

<div class="min-h-screen py-10">
  <section class="mx-auto max-w-7xl px-4">
    <h1 class="mb-8 text-3xl font-bold text-slate-800">
      Cartoon Categories
    </h1>

    <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-7">
      {#each data.categories as category (category.id)}
        <a
          href={resolve(`/category/${category.id}`)}
          class="group overflow-hidden rounded-xl bg-white shadow-md transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
          data-sveltekit-preload-data="hover"
        >
          <img
            src={category.r2_category_image_key}
            alt={category.name}
            class="aspect-square w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />

          <div class="p-4">
            <h2 class="text-center font-semibold text-slate-700 cursor-pointer">
              {category.name}
            </h2>
          </div>
         </a>
      {/each}
    </div>
  </section>
</div>