<template>
    <div class="dashboard-container">
      <div v-if="store.state.pipelines.length != 0" class="dashboard-container">
        <div v-for="(o, index) in store.state.pipelines.length" :key="o">
          <el-card class="stream-card" :body-style="{ padding: '10px' }">
            <div>
              <StreamView style="width: 90%; height: 90%; padding: 10px"
                :stream="{name: store.state.pipelines[index].stream_name,
                         url: store.state.stream_urls[index]}"
                />
            </div>
            <div style="padding: 14px">
              <span>{{ store.state.pipelines[index]['pipeline_id'] }}</span>
            </div>
          </el-card>
        </div>
      </div>
      <div v-else style="margin: auto auto">
      <h1>No pipeline found from database server</h1>
      <p/>
      <h3>{{ store.state.pipeline_db_server }}</h3>
    </div>
    </div>
</template>

<script setup lang="ts">
import StreamView from '../components/StreamView.vue';
import { useStore } from 'vuex';
import { onMounted, onUnmounted } from 'vue';
import { refreshPipeline } from "../store";

const store = useStore();

onMounted(() => {
  console.log("Dashboard View: onMounted");
  refreshPipeline(store.state.pipeline_db_server, store.state.websocket_server);
})

onUnmounted(() => {
  console.log("Dashboard View: onUnMounted");
})
</script>

<style scoped>
.dashboard-container {
  margin: 5px;
  display: flex;
  flex-wrap: wrap;
  min-height: 600px;
}

.stream-card {
  width: 400px;
  margin: 5px;
  font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
  font-size: large;
}

.time {
  font-size: 12px;
  color: #999;
}

.bottom {
  margin-top: 5px;
  line-height: 5px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.button {
  padding: 0;
  min-height: auto;
}

.image {
  width: 100%;
  display: block;
}
</style>
