# Cloud Native AI Pipeline

![CI Check License](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-license-check.yaml/badge.svg)
![CI Check Spelling](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-doclint.yaml/badge.svg)
![CI Check Python](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-pylint.yaml/badge.svg)
![CI Check Shell](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-shell-check.yaml/badge.svg)

_(Disclaimer: This project is currently under active development, and as such, all source code may not be included in any release. This means that the code is subject to change without notice, and that any information contained within the code should be considered as work in progress.)_

## 1. Overview

This project provides a multiple-stream, real-time inference pipeline based on cloud native design pattern as following architecture
diagram:

![](docs/cnap_arch.png)

Cloud-native technologies can be applied to Artificial Intelligence (AI) for scalable application in dynamic environments
such as public, private and hybrid cloud. But it requires a cloud native design to decompose monolithic inference pipeline
into several microservices:

| Microservice | Role | Description  |
| ------------ | ---- | ----------- |
| Transcoding Gateway | Data Source | Receive multiple streams and perform transcoding |
| Frame Queue | Data Integration | Assign the input stream into specific work queue |
| Infer Engine | Data Analytics | Infer the frame and send result to result broker |
| Dashboard | Data Visualization | Render the result into client's single page application |

## 2. Usages

It is be extend for the following uses:

- End-to-End Macro Bench Framework for cloud native pipeline like DeathStar Bench
- Trusted AI pipeline to protect input stream or model in TEE VN/Container
- Sustainable AI computing to reduce carbon footprint for AI workloads

![](docs/cnap-uses.png)
