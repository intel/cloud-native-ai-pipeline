<template>
    <iframe :src="getSrc()" height="800px" width="100%"></iframe>
</template>

<script setup lang="ts">
import { useStore } from 'vuex';
import { onMounted, onUnmounted } from 'vue';
import { refreshPipeline } from "../store";

const store = useStore();

function getSrc() {
    return store.state.grafana_server + '/dashboards';
}

onMounted(() => {
  console.log("Grafana View: onMounted");
  refreshPipeline();
})

onUnmounted(() => {
  console.log("Grafana View: onUnMounted");
})
</script>
