<script lang="ts" setup>
import cnap_logo from "../assets/cnap_logo.png"
</script>

<template>
    <div class="app-foot">
        <div class="app-foot-child">
            Created by <a href='https://wiki.ith.intel.com/display/csecss/Cloud+Stack+Solution+Home'>Intel/SATG/SSE/Cloud Stack Solution</a> Team
        </div>
        <div class="app-foot-child">
            <el-image class="cnap-logo" :src="cnap_logo"/>
        </div>
    </div>

</template>

<style scoped>

.app-foot {
    background: #F0F2F5;
    text-align: center;
    height: 100px;
    display: flex;
    justify-content: center;
}
.app-foot-child {
    margin-right: 10px;
    margin-top: auto;
    margin-bottom: auto;
}
.cnap-logo {
    width: 30px;
    height: 30px;
}
</style>
