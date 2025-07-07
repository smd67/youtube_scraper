<!-- DataTable.vue -->
<template>
    <div class="my-division">
      <div class="my-division">
        <Input @button-clicked="fetchTableData" @data-sent="handleData"/>
      </div>
      <div class="my-grid" v-if="tableData.length > 0">
        <div class="grid-item"><BarChart id="1" dataset_label="Videos" dataset_color="red" :labels="titles" :data="videos"/></div>
        <div class="grid-item"><BarChart id="2" dataset_label="Subscribers" dataset_color="blue" :labels="titles" :data="subscribers"/></div>
        <div class="grid-item"><BarChart id="3" dataset_label="Sentiment" dataset_color="green" :labels="titles" :data="sentiment" /></div>
        <div class="grid-item"><BarChart id="3" dataset_label="Relevance" dataset_color="orange" :labels="titles" :data="relevance" /></div>
      </div>
      <div class="spinner" v-if="isLoading"></div>
      <div>
        <table v-if="tableData.length > 0">
            <thead>
            <tr>
                <th>Title</th>
                <th>Url</th>
                <!-- Add more table headers as needed -->
            </tr>
            </thead>
            <tbody>
            <tr v-for="item in tableData" :key="item.Title">
                <td>{{ item.Title }}</td>
                <td><a v-bind:href="item.Url" target="_blank">{{ item.Url }}</a></td>
                <!-- Display more data properties as needed -->
            </tr>
            </tbody>
        </table>
      </div>
    </div>
  </template>

  <script>
  import axios from 'axios';
  import Input from './Input.vue';
  import BarChart from './BarChart.vue';

  export default {
    components: { Input, BarChart},
    data() {
      return {
        tableData: [], // This array will store the fetched data
        queryString: '',
        titles: [],
        videos: [],
        subscribers: [],
        sentiment: [],
        relevance: [],
        isLoading: false,
      };
    },
    methods: {
      handleData(data) {
        this.queryString = data;
      },
      async fetchTableData() {
        const apiUrl = 'http://127.0.0.1:8000/query/'; // Replace with your actual API endpoint
        const config = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        const requestBody = {
            query_string: this.queryString
        }
        try {
          this.isLoading = true;
          const response = await axios.post(apiUrl, requestBody, config);
          this.titles = response.data.map(obj => obj.Title);
          this.videos = response.data.map(obj => obj.Videos);
          this.subscribers = response.data.map(obj => obj.Subscribers);
          this.sentiment = response.data.map(obj => obj.Score);
          this.relevance = response.data.map(obj => obj.Similarity);
          this.tableData = response.data; // Assign the fetched data to tableData
        } catch (error) {
          console.error('Error fetching data:', error);
        } finally {
          this.isLoading = false;
        }
      },
    },
  };
  </script>

  <style scoped>
  /* Add basic styling for the table if needed */
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  th {
    background-color: #f2f2f2;
  }
  .my-division {
    padding-top: 30px;
    padding-bottom: 30px;
  }
  .my-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr); /* 2 columns, equal width */
      grid-template-rows: repeat(2, auto); /* 2 rows, height determined by content */
      gap: 10px; /* Adjust as needed for spacing */
      padding-bottom: 30px;
    }
  .grid-item {
    /* Optional: Add styling for individual grid items */
    border: 1px solid #ccc;
    padding: 10px;
  }
  .spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
  </style>