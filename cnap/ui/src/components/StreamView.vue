<template>
    <div class="stream-card">
        <div class="stream-view">
            <div class="stream-name">
                <h3>{{ streamTitle }}</h3>
            </div>
            <img :id="stream.name" ref="imgRef" style="width: 98%; height: 85%;">
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, Ref, VNodeRef } from 'vue';
import { FrameMessage } from '../api/frame.js';

interface Stream {
    name: string,
    url: string
}

export interface Latency {
    s2i_latency: number,
    i2u_latency: number
}

const props = defineProps<{
    stream: Stream
}>();

const socket = ref<WebSocket | null>(null);
const imgRef: Ref<VNodeRef | undefined>['value'] = ref(undefined);
let intervalId: number;

const streamTitle = computed(() => {
    return props.stream.name.split(":")[0];
});

const connectWebsocketServer = () => {
    const url = props.stream.url.replace("http", props.stream.url.startsWith("https") ? "wss" : "ws");
    var ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    const img = imgRef;

    if (!img.value) {
        console.error("Image reference is null. Ensure the element is rendered");
        return;
    }

    img.value.onload = function() {
        URL.revokeObjectURL(this.src);
    };

    ws.onopen = function(evt) {
        console.log("websocket onopen!");
    };
    ws.onclose = function(evt) {
        console.log("websocket onclose!");
    };
    ws.onerror = function(err) {
        console.error("websocket error!", err);
    };
    ws.onmessage = function(e) {
        const frame = FrameMessage.decode(new Uint8Array(e.data))
        const imgData = frame.raw
        URL.revokeObjectURL(img.value.src);
        img.value.src = URL.createObjectURL(new Blob([imgData], { type: 'image/jpg' }));

        const time_now : number = new Date().getTime();
        const s2i_latency = (frame.tsInferEnd - frame.tsNew) * 1000;
        const i2u_latency = time_now - frame.tsInferEnd * 1000;
        const latency: Latency = {s2i_latency: s2i_latency, 
                                   i2u_latency: i2u_latency};
        emit("onReceiveMsg", latency);
    }
    socket.value = ws;
};

const closeWebsocket = () => {
    if(socket.value) {
        socket.value.close();
    }
};

const emit = defineEmits(["onReceiveMsg"]);

onMounted(() => {
    connectWebsocketServer();
    intervalId = window.setInterval(closeWebsocket, 10 * 60 * 1000);
});

onUnmounted(() => {
    window.clearInterval(intervalId);
    closeWebsocket();
});

</script>

<style scoped lang="less">
    .stream-card {
        height: 100%;
        width: 100%;
        display: flex;
        background-color: lightyellow;
    }
    .stream-name {
        height: 30px;
        margin-left: auto;
        margin-right: auto;
    }
    .stream-view {
        height: 100%;
        width: 100%;
    }
</style>
