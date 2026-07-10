<script lang="ts">
    const categories = [
    {
        id: 1,
        name: "হাস্যরস",
        image: "https://picsum.photos/seed/bengali-cartoon-1/400/300"
    },
    {
        id: 2,
        name: "অ্যাডভেঞ্চার",
        image: "https://picsum.photos/seed/bengali-cartoon-2/400/300"
    },
    {
        id: 3,
        name: "রূপকথা",
        image: "https://picsum.photos/seed/bengali-cartoon-3/400/300"
    },
    {
        id: 4,
        name: "বিজ্ঞান কল্পকাহিনী",
        image: "https://picsum.photos/seed/bengali-cartoon-4/400/300"
    },
    {
        id: 5,
        name: "সুপারহিরো",
        image: "https://picsum.photos/seed/bengali-cartoon-5/400/300"
    },
    {
        id: 6,
        name: "ভৌতিক",
        image: "https://picsum.photos/seed/bengali-cartoon-6/400/300"
    },
    {
        id: 7,
        name: "শিক্ষামূলক",
        image: "https://picsum.photos/seed/bengali-cartoon-7/400/300"
    },
    {
        id: 8,
        name: "প্রাণীজগৎ",
        image: "https://picsum.photos/seed/bengali-cartoon-8/400/300"
    },
    {
        id: 9,
        name: "লোককাহিনী",
        image: "https://picsum.photos/seed/bengali-cartoon-9/400/300"
    },
    {
        id: 10,
        name: "পারিবারিক",
        image: "https://picsum.photos/seed/bengali-cartoon-10/400/300"
    },
    {
        id: 11,
        name: "রহস্য",
        image: "https://picsum.photos/seed/bengali-cartoon-11/400/300"
    },
    {
        id: 12,
        name: "ক্রীড়া",
        image: "https://picsum.photos/seed/bengali-cartoon-12/400/300"
    }
    ];


</script>

<div class="bg-slate-50 min-h-screen py-10">
  <section class="mx-auto max-w-7xl px-4">
    <h1 class="mb-8 text-3xl font-bold text-slate-800">
      কার্টুন ক্যাটাগরি
    </h1>

    <div class="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-7">
      {#each categories as category (category.id)}
        <div
          class="group overflow-hidden rounded-2xl bg-white shadow-md transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
        >
          <img
            src={category.image}
            alt={category.name}
            class="aspect-square w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />

          <div class="p-4">
            <h2 class="text-center font-semibold text-slate-700">
              {category.name}
            </h2>
          </div>
        </div>
      {/each}
    </div>
  </section>
</div>