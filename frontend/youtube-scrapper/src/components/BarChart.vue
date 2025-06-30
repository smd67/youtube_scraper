<template>
    <Bar :data="chartData" :options="chartOptions" />
</template>
  
<script>
  import { Bar } from 'vue-chartjs';
  import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
  
  ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);
  
  export default {
    name: 'BarChart',
    components: { Bar },
    props: {
      id: {
        type: Number,
        default: 1,
      },
      dataset_label: {
        type: String,
        default: "Sales",
      },
      dataset_color: {
        type: String,
        default: '#f87979',
      },
      labels: {
        type: Array,
        default: () => ['January', 'February', 'March', 'April', 'May']
      },
      data: {
        type: Array,
        default: () => [40, 20, 12, 39, 10]
      }
    },
    data() {
      return {
        chartOptions: {
          responsive: true,
          maintainAspectRatio: false
        },
      };
    },
    computed: {
        chartData() {
          return {
          labels: this.labels,
          datasets: [
            {
              label: this.dataset_label,
              backgroundColor: this.dataset_color,
              data: this.data,
            },
          ],
        }
      }
    }
  };
  </script>