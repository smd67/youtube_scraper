<template>
  <header>
    <img alt="Vue logo" class="logo" src="./assets/youtube_logo.png" width="125" height="125" />
    <div class="wrapper">
      <HelloWorld msg="YouTube Channel Recommender" :titles="titles" :videos="videos" :subscribers="subscribers" :sentiment="sentiment" :relevance="relevance" />
    </div>
  </header>

  <main>
    <DataTable @table-data-fetched="handleTableData" />
  </main>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import DataTable from './components/DataTable.vue';

export default {
    components: { HelloWorld, DataTable },
    data() {
      return {
        titles: [],
        videos: [],
        subscribers: [],
        sentiment: [],
        relevance: []
      };
    },
    methods: {
      handleTableData(data){
        this.titles = data.titles;
        this.videos = data.videos;
        this.subscribers = data.subscribers;
        this.sentiment = data.sentiment;
        this.relevance = data.relevance;
      }
    }
};
</script>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
    margin-top: 30px; /* Adjust the value as needed */
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
