# QAT Integration Documentation

This document delineates the integration of Intel® QuickAssist Technology ([Intel® QAT](https://www.intel.com/content/www/us/en/developer/topic-technology/open/quick-assist-technology/overview.html)) within the Cloud Native AI Pipeline. Using Intel® QAT in Cloud Native AI Pipeline to accelerate the compression and decompression of image frames can improve peformance and power efficiency.

## Table of Contents

- [Overview](#overview)
- [Install QAT As Non-root User on host](#install-qat-as-non-root-user-on-host)
- [Setup QAT Device Plugin](#setup-qat-device-plugin)
- [Configuration for Containerd](#configuration-for-containerd)
- [Configuration in Cloud Native AI Pipeline](#configuration-in-cloud-native-ai-pipeline)
- [Resources](#resources)

## Overview

[Intel® QAT](https://www.intel.com/content/www/us/en/developer/topic-technology/open/quick-assist-technology/overview.html) offloads computationally intensive symmetric and asymmetric cryptography and data compression/decompression operations from the CPU, relieving the CPU from these demanding tasks. This reallocation of computational resources allows the CPU to perform other tasks more efficiently, potentially enhancing overall system performance, efficiency, and power across various use cases.

## Install QAT As Non-root User on host

Please refer to https://www.intel.com/content/www/us/en/content-details/632506/intel-quickassist-technology-intel-qat-software-for-linux-getting-started-guide-hardware-version-2-0.html section "3.8 Running Applications as Non-Root User".

## Setup QAT Device Plugin

Please refer to https://github.com/intel/intel-device-plugins-for-kubernetes/blob/main/cmd/qat_plugin/README.md.

## Configuration for Containerd

Configure LimitMEMLOCK for containerd:
```bash
sudo systemctl edit containerd

# Add this text
[Service]
LimitMEMLOCK=infinity

sudo systemctl daemon-reload
sudo systemctl restart containerd
```

## Configuration in Cloud Native AI Pipeline

Add QAT resources in [streaming service](../helm/stream/values.yaml#L30) and [inference service](../helm/inference/values.yaml#L34):
```
resources:
  limits:
    qat.intel.com/cy0_dc1: 1
```

In order to compress and decompress image frame using QAT in Cloud Native AI Pipeline, the env need to be added in [streaming service](../helm/stream/values.yaml#L52) and [inference service](../helm/inference/values.yaml#L56):
```
- name: ZIP_ENABLE
    value: true
- name: ZIP_TOOL
    value: QAT
```

## Resources

- [Intel® QuickAssist Technology (Intel® QAT)](https://www.intel.com/content/www/us/en/developer/topic-technology/open/quick-assist-technology/overview.html)
- [Intel® Device Plugin for Kubernetes](https://github.com/intel/intel-device-plugins-for-kubernetes)
