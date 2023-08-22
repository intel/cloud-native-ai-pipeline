<template>
  <div class="pipelines-container">
    <div style="width: 100%;" v-if="store.state.pipelines.length != 0">
      <el-row>
        <el-col v-for="(o, index) in store.state.pipelines.length" :key="o" >
          <el-card class="stream-card" :body-style="{ width: '100%', padding: '10px' }">
            <div>
              <DetailView
                :pipeline_id="store.state.pipelines[index].pipeline_id"
                :stream_name="store.state.pipelines[index].stream_name"
                :model_name="store.state.pipelines[index].model_name"
                :input_fps="store.state.pipelines[index].input_fps"
                :infer_fps="store.state.pipelines[index].infer_fps"
                :stream_url="store.state.stream_urls[index]"
                :now_time="store.state.now_time"
                />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    <div v-else style="margin: auto auto">
      <h1>No pipeline found from database server</h1>
      <p/>
      <h3>{{ store.state.pipeline_db_server }}</h3>
    </div>
  </div>
</template>

<script setup lang="ts">
import DetailView from '../components/DetailView.vue';
import { useStore } from 'vuex';
import { onMounted, onUnmounted } from 'vue';
import { refreshPipeline } from "../store";
const store = useStore();

onMounted(() => {
  console.log("Pipeline View: onMounted");
  refreshPipeline(store.state.pipeline_db_server, store.state.websocket_server);
})

onUnmounted(() => {
  console.log("Pipeline View: onUnMounted");
})
</script>

<style scoped>
.pipelines-container {
  min-height: 600px;
  display: flex;
}

.stream-card {
  width: 100%;
  height: 250px;
  margin: 10px;
  display: flex;
}

.image {
  width: 40%;
  display: block;
}
</style>
