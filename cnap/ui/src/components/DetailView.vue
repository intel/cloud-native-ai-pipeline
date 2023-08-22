<template>
  <el-row :gutter="20">
    <el-col :span="4">
        <div class="grid-content ep-bg-purple" >
          <StreamView style="width: 90%; height: 80%; text-align: center;"
            :stream="{name: stream_name,
                      url: stream_url}"
           />
        </div>
    </el-col>
    <el-col :span="12">
      <div class="grid-content">
        <el-row :gutter="20" class="line-item">
            <el-col  :span="5">
              <div style="text-align: left;">
                <el-text size="large">Pipeline ID</el-text>
              </div>
            </el-col>
            <el-col :span="19">
              <div style="text-align: left;">
                {{ pipeline_id }}
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="line-item">
            <el-col :span="5">
              <div style="text-align: left;">
                <el-text size="large">Model Name</el-text>
              </div>
            </el-col>
            <el-col :span="19">
              <div style="text-align: left;">
                <el-text size="large">{{ model_name }}</el-text>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="line-item">
            <el-col :span="5">
              <div style="text-align: left;">
                <el-text size="large">Stream Name</el-text>
              </div>
            </el-col>
            <el-col :span="19">
              <div style="text-align: left;">
                <el-text size="large">{{ stream_name }}</el-text>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="line-item">
            <el-col :span="5">
              <div style="text-align: left;">
                <el-text size="large">Input Speed</el-text>
              </div>
            </el-col>
            <el-col :span="19">
              <div style="text-align: left;">
                <el-text size="large"> {{ input_fps }} (FPS)</el-text>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="line-item">
            <el-col :span="5">
              <div style="text-align: left;">
                <el-text size="large">Infer Speed</el-text>
              </div>
            </el-col>
            <el-col :span="19">
              <div style="text-align: left;">
                <el-text size="large">{{ infer_fps }} (FPS)</el-text>
              </div>
            </el-col>
          </el-row>
      </div>
    </el-col>
    <el-col :span="4">
      <div class="grid-content" >
        <vue-echarts class="line" :option="state.overviewOption" ref="chart" style="height: 90%; width: 90%;"/>
      </div>
    </el-col>
    <el-col :span="4">
      <div class="grid-content" >
        <vue-echarts class="line" :option="getOption()" ref="chart" style="height: 90%; width: 90%;"/>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue';
import StreamView from './StreamView.vue';
import { VueEcharts } from 'vue3-echarts';
import type { EChartsOption } from 'echarts';

const props = defineProps({
  pipeline_id: {
    type: String,
    default: ''
  },
  model_name: {
    type: String,
    default: 'dummy model',
  },
  stream_name: {
    type:String,
    default: 'dummy stream'
  },
  input_fps: {
    type: Number,
    default: 0
  },
  infer_fps: {
    type: Number,
    default: 0
  },
  stream_url: {
    type: String,
    default: 'dummy url'
  },
  now_time: {
    type: String,
    default: ""
  }
});

const state = reactive({
  overviewOption: {},
  dataCenterTime: []
})

const max_points = 5;

const data_source : Array<[string, number, number]>= [];

function getOption() : EChartsOption {
  data_source.push([props.now_time, props.infer_fps, Math.max(props.input_fps - props.infer_fps, 0)]);
  if (data_source.length > max_points) {
    data_source.splice(0, 1);
  }

  return {
    legend: {},
    tooltip: {},
    dataset: {
        dimensions:  ['product', 'Infer FPS', 'Drop FPS'],
        source: data_source
    },
    color: ['#007bff', '#dc3545', '#007bff'],
    xAxis: {
        type: 'category',
        axisTick: {
            show: false
        },
    },
    yAxis: {
        show: true,
        axisTick: {
            show: false
        },
        axisLine: {
            show: false
        },
        splitLine: {
            show: true
        },
    },
    series: [
        {type: 'line'},
        {type: 'line'},
        {type: 'line'}
    ]
  }
}

onMounted(() => {
  state.overviewOption = {
        legend: {},
        tooltip: {},
        dataset: {
            dimensions:  ['product', 'AMX', 'VNNI', 'Normal'],
            source: [
                ['1:00', 43.3, 55.8, 93.7],
                ['2:00', 42.1, 73.4, 95.1],
                ['3:00', 34.4, 65.2, 82.5],
            ]
        },
        color: ['#20c997', '#007bff', '#dc3545'],
        xAxis: {
            type: 'category',
            axisTick: {
                show: false
            },
        },
        yAxis: {
            show: true,
            axisTick: {
                show: false
            },
            axisLine: {
                show: false
            },
            splitLine: {
                show: true
            },
        },
        series: [
            {type: 'bar'},
            {type: 'bar'},
            {type: 'bar'}
        ]
    }
})
</script>

<style>
.grid-field {
  margin: 10px;
  align-content: left;
  text-align: left;
}

.line-item {
  margin: 20px;
}

.grid-content {
  border-radius: 4px;
  min-height: 120px;
  height: 100%;
  text-align: left;
}

.image {
  width: 100%;
  height: 95%;
  display: block;
}
</style>
