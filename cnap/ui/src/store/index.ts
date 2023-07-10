import { createStore } from 'vuex'
import { App } from 'vue'
import { Pipeline } from '../api/ppdb_api';
import axios  from "axios";

const store = createStore<{pipelines:Pipeline[], stream_urls:string[],
        pipeline_db_server:string, websocket_server:string}>({
  state() {
    return {
      pipelines: [],
      stream_urls: [],
      // To prevent accidentally leaking env variables to the client, only variables prefixed
      // with `VITE_` are exposed to Vite-processed code.
      pipeline_db_server: 'http://' + get_env('VITE_PPDB_SERVER_HOST', window.location.hostname)
                            + ':' + get_env('VITE_PPDB_SERVER_PORT', 5000) + '/api/pipelines',
      websocket_server: 'ws://' + get_env('VITE_WS_SERVER_HOST', window.location.hostname)
                            + ':' + get_env('VITE_WS_SERVER_PORT', 31611)
    }
  },
  mutations: {
    updatePipelines(state, payload) {
      state.pipelines = payload.pipelines
      state.stream_urls = payload.urls
      state.pipeline_db_server = payload.db_server
      state.websocket_server = payload.ws_server
    },
    cleanPipelines(state, payload) {
      state.pipelines = []
      state.stream_urls = []
      state.pipeline_db_server = payload.db_server
      state.websocket_server = payload.ws_server
    }
  },
});

export const initStore = (app: App<Element>) => {
  app.use(store);
}

export const refreshPipeline = async (pipeline_db_url:string, ws_server_url:string) => {
  console.log("Refresh pipeline from", pipeline_db_url);
  try {
    const res = await axios.get(pipeline_db_url);
    let urls = [];
    for (let pipeline of res.data) {
      urls.push(ws_server_url + "/" + pipeline.pipeline_id);
    }
    store.commit('updatePipelines',
      {'db_server': pipeline_db_url, 'ws_server': ws_server_url,
        'pipelines': res.data, 'urls': urls});
  } catch (error) {
    console.log(error);
    store.commit('cleanPipelines', {'db_server': pipeline_db_url, 'ws_server': ws_server_url});
  }
}

function get_env(key:string, default_vaule:any = null) {
  let value = import.meta.env[key];
  if (value == null) {
    console.log("Cloud not find the key %s in environment, use default value %s", 
                key, String(default_vaule));
    return default_vaule;
  }
  return value;
}
