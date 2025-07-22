<template>
    <Bar :data="chartData" :options="chartOptions" />
</template>
  
<script>
  import { Bar } from 'vue-chartjs';
  import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
  import { palettes } from './palettes.js'

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
      palette: {
        type: String,
        default: "school_bust",
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
        palettes: palettes,
        chartOptions: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: true, // Set to true to display the title
              text: this.dataset_label, // The actual title text
              font: {
                style: 'italic',
                weight: 'bold',
              }
            }
          }
        },
      };
    },
    computed: {
        chartData() {   
          return {
            labels: this.labels,
            datasets: [
              {
                backgroundColor: this.palettes[this.palette],
                data: this.data,
              },
            ],
          }
      }
    }
  };
  </script>