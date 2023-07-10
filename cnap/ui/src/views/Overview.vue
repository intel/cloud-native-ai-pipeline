<template>
  <div >
    <el-carousel class="overview-container" height="800px" arrow="always"
      :pause-on-hover="false">
      <el-carousel-item>
        <h1>Cloud Native Design for Micro/Macro Bench</h1>
        <el-image
        style="width: 100%; height: 600px"
        :src="cloud_native_design_img"
        fit="contain"
        loading="lazy"
        />
      </el-carousel-item>
      <el-carousel-item>
        <h1>Carbon Footprint for Kubernetes</h1>
        <el-image
        style="width: 100%; height: 600px"
        :src="carbon_footprint_img"
        fit="contain"
        loading="lazy"
        />
      </el-carousel-item>
      <el-carousel-item>
        <h1>Trusted Design to Protect input and Model</h1>
        <el-image
        style="width: 100%; height: 600px"
        :src="trusted_pipeline_img"
        fit="contain"
        loading="lazy"
        />
      </el-carousel-item>
      <el-carousel-item>
        <h1>Landing on Diverse Cloud Native Framework</h1>
        <el-image
        style="width: 100%; height: 600px"
        :src="diverse_frameworks_img"
        fit="contain"
        loading="lazy"
        />
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<script setup lang="ts">
import trusted_pipeline_img from '../assets/trusted_pipeline.png'
import cloud_native_design_img from '../assets/pipeline_cloud_native_design.png'
import diverse_frameworks_img from '../assets/diverse_frameworks.png'
import carbon_footprint_img from '../assets/carbon_footprint.png'
</script>

<style scoped>
.overview-container {
  margin: 5px 5px 5px 5px;
  border: 1px red solid;
}
</style>
