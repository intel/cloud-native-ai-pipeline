<template>
  <el-config-provider namespace="ep">
    <AppHeader />
    <router-view/>
    <AppFooter />
  </el-config-provider>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { refreshPipeline, closeEventSource } from "./store";

onMounted(async () => {
  console.log("app mounted");
  refreshPipeline();
});

onBeforeUnmount(() => {
  closeEventSource();
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
