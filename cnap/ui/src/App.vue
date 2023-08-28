<template>
  <el-config-provider namespace="ep">
    <AppHeader />
    <router-view/>
    <AppFooter />
  </el-config-provider>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue';
import axios, { AxiosInstance } from "axios";
import { useStore } from 'vuex';
import { refreshPipeline } from "./store";

const store = useStore();

onMounted(async () => {
  console.log("app mounted");
  setInterval(refreshPipeline, 1000);
});


</script>

<style>
#app {
  text-align: center;
  color: var(--ep-text-color-primary);
}

.element-plus-logo {
  width: 50%;
}
</style>
