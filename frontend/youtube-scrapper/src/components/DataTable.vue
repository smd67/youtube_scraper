<!-- DataTable.vue -->
<template>
    <div class="my-division">
      <div class="my-division">
        <Input @button-clicked="fetchTableData" @data-sent="handleData"/>
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

  export default {
    components: { Input },
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
          this.titles = response.data.map(obj => obj.Title.slice(0, 20));
          this.videos = response.data.map(obj => obj.Videos);
          this.subscribers = response.data.map(obj => obj.Subscribers);
          this.sentiment = response.data.map(obj => obj.Score);
          this.relevance = response.data.map(obj => obj.Similarity);
          this.tableData = response.data; // Assign the fetched data to tableData
          this.$emit('table-data-fetched', {
            titles: this.titles, 
            videos: this.videos, 
            subscribers: this.subscribers, 
            sentiment: this.sentiment, relevance: this.relevance
          });
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
    padding-top: 90px;
    padding-bottom: 30px;
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