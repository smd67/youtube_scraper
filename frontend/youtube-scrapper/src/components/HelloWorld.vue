<template>
  <div class="greetings">
    <h1 class="green">{{ msg }}</h1>
    <h3>
      Project created with
      <a href="https://vite.dev/" target="_blank" rel="noopener">Vite</a> +
      <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue 3</a>.
    </h3>
  </div>
  <div>
    <div class="my-grid" v-if="titles.length > 0">
      <div class="grid-item"><PieChart dataset_label="Videos" palette="booming_neon" :labels="titles" :data="videos" /></div>
      <div class="grid-item"><PieChart dataset_label="Subscribers" palette="booming_neon" :labels="titles" :data="subscribers" /></div>
    </div>
    <div class="my-grid" v-if="titles.length > 0">
        <div class="grid-item"><BarChart dataset_label="Sentiment" palette="booming_neon" :labels="titles" :data="sentiment" /></div>
        <div class="grid-item"><BarChart dataset_label="Relevance" palette="booming_neon" :labels="titles" :data="relevance" /></div>
    </div>
  </div>
</template>

<script>
  import BarChart from './BarChart.vue';
  import PieChart from './PieChart.vue';

  export default {
    components: { BarChart, PieChart},
    props: {
      msg: {
        type: String,
        required: true,
      },
      titles: {
        type: Array,
        default: () => []
      },
      videos: {
        type: Array,
        default: () => []
      },
      subscribers: {
        type: Array,
        default: () => []
      },
      sentiment: {
        type: Array,
        default: () => []
      },
      relevance: {
        type: Array,
        default: () => []
      },
    },
  }
</script>

<style scoped>
h1 {
  font-weight: 500;
  font-size: 2.6rem;
  position: relative;
  top: -10px;
}

h3 {
  font-size: 1.2rem;
}

.greetings h1,
.greetings h3 {
  text-align: center;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: left;
  }
}

.my-grid {
  padding-top: 30px;
  display: grid;
  min-height: 400px;
  grid-template-columns: repeat(2, 1fr); /* 2 columns, equal width */
  grid-template-rows: repeat(1, auto); /* 2 rows, height determined by content */
  gap: 10px; /* Adjust as needed for spacing */
  padding-bottom: 30px;
}
.grid-item {
  /* Optional: Add styling for individual grid items */
  border: 1px solid #ccc;
  padding: 10px;
}
</style>
