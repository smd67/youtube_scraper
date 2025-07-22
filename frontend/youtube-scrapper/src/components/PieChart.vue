<template>
  <Pie :data="chartData" :options="chartOptions" />
</template>
  
<script>
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'vue-chartjs'
import { palettes } from './palettes.js'

ChartJS.register(ArcElement, Tooltip, Legend);

export default {
  name: 'PieChart',
  components: {
    Pie
  },
  props: {
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
        plugins: {
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
            label: this.dataset_label,
            backgroundColor: this.palettes[this.palette],
            data: this.data,
          },
        ],
      }
    }
  }
};
</script>