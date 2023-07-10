
<template>
  <el-menu class="header-menu" mode="horizontal" :ellipsis="false" :router="true"
    background-color="#F0F2F5">
    <el-menu-item index="/" route="/">
        <h3>Overview</h3>
    </el-menu-item>
    <el-menu-item index="/dashboard" route="/dashboard">
      <h3>Dashboard</h3>
    </el-menu-item>
    <el-menu-item index="/Pipelines" route="/pipelines">
      <h3>Pipelines</h3>
    </el-menu-item>
    <div class="flex-grow" />
    <el-menu-item class="app-logo" @click="dialogConfigVisible=true">
      <h2>Cloud-Native AI Pipeline</h2>
    </el-menu-item>

    <el-dialog
      v-model="dialogConfigVisible"
      title="Backend Server (BaaS) Configurations"
      >
      <el-form :model="form">
        <el-form-item label="Pipeline DB" :label-width="formLabelWidth">
          <el-input v-model="form.pipeline_db_server" autocomplete="off" />
        </el-form-item>
        <el-form-item label="WebSocket" :label-width="formLabelWidth">
          <el-input v-model="form.websocket_server" autocomplete="off" />
        </el-form-item>
        <el-form-item label="Grafana" :label-width="formLabelWidth"  >
          <el-input v-model="form.grafana_server" autocomplete="off" :disabled="true"/>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogConfigVisible = false">Cancel</el-button>
          <el-button type="primary" @click="handleClose">
            Confirm
          </el-button>
        </span>
      </template>

    </el-dialog>
  </el-menu>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useStore } from 'vuex';
import { refreshPipeline } from '../store';

const store = useStore();

const dialogConfigVisible = ref(false);
const formLabelWidth = '120px'
const form = reactive({
  pipeline_db_server: store.state.pipeline_db_server,
  websocket_server: store.state.websocket_server,
  grafana_server: '',
})

const handleClose = () => {
  console.log("handleDialogClose");
  dialogConfigVisible.value = false;
  console.log("Pipeline DB Server: %s", String(form.pipeline_db_server));
  console.log("Websocket Server: %s", String(form.websocket_server));
  refreshPipeline(form.pipeline_db_server, form.websocket_server);
}
</script>

<style scoped>
.flex-grow {
  flex-grow: 1;
}

.app-logo {
  height: 100%;
  text-align: center;
}

</style>
