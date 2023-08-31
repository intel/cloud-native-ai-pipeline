<template>
  <el-row :gutter="20">
    <el-col :span="4">
        <div class="grid-content ep-bg-purple" >
          <StreamView style="width: 90%; height: 80%; text-align: center;"
            :stream="{name: stream_name,
                      url: stream_url}"
            @onReceiveMsg="onReceiveMsg"
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
        <vue-echarts class="bar" :option="getOption_latency()" ref="chart" style="height: 90%; width: 90%;"/>
      </div>
    </el-col>
    <el-col :span="4">
      <div class="grid-content" >
        <vue-echarts class="line" :option="getOption_fps()" ref="chart" style="height: 90%; width: 90%;"/>
      </div>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import StreamView, { Latency } from './StreamView.vue';
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

const max_points = 5;

const s2i_latency_array: Array<number> = [];
const i2u_latency_array: Array<number> = [];

const data_source_fps: Array<[string, number, number]>= [];
const data_source_latency: Array<[string, number, number]>= [];

function getOption_latency(): EChartsOption {
  const average = (arr: Array<number>) => arr.reduce((acc, val) => acc + val, 0) / arr.length;
  data_source_latency.push([props.now_time, average(s2i_latency_array), average(i2u_latency_array)]);
  s2i_latency_array.splice(0);
  i2u_latency_array.splice(0);
  if (data_source_latency.length > max_points) {
    data_source_latency.splice(0, 1);
  }

  return {
      legend: {},
      tooltip: {},
      dataset: {
          dimensions:  ['product', 'Stream->Infer', 'Infer->UI'],
          source: data_source_latency
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
          name: "Latency(ms)",
      },
      series: [
          {type: 'bar'},
          {type: 'bar'},
      ],
      stack: '1',
      grid: {
        left: '5%',
        right: '2%',
        bottom: '10',
        containLabel: true,
      }
  }
}

function getOption_fps() : EChartsOption {
  data_source_fps.push([props.now_time, props.infer_fps, Math.max(props.input_fps - props.infer_fps, 0)]);
  if (data_source_fps.length > max_points) {
    data_source_fps.splice(0, 1);
  }

  return {
    legend: {},
    tooltip: {},
    dataset: {
        dimensions:  ['product', 'Infer FPS', 'Drop FPS'],
        source: data_source_fps
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
    ],
    grid: {
        left: '5%',
        right: '2%',
        bottom: '10',
        containLabel: true,
      }
  }
}

const onReceiveMsg = (params: Latency) => {
  s2i_latency_array.push(params.s2i_latency);
  i2u_latency_array.push(params.i2u_latency);
}

onMounted(() => {
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
