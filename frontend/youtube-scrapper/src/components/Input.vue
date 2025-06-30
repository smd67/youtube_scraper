<template>
  <button @click="triggerAction" class="my-button">Submit</button>
  <input type="text" v-model="queryString" @keyup.enter="triggerAction" placeholder="Enter text here" class="my-input" />
</template>
  
<script>
  export default {
    data() {
      return {
        queryString: ''
      };
    },
    methods: {
      triggerAction() {
        this.$emit('data-sent', this.queryString);
        this.$emit('button-clicked'); // Emit a custom event
      }
    }
  }
</script>

<style scoped>
.my-button {
  margin-right: 5px;
  height: 30px;
}
.my-input {
  height: 30px;
  width: 500px;
}
</style>