# Cloud Native AI Pipeline

_(Disclaimer: This project is currently under active development, and as such, all source code may not be included in any release. This means that the code is subject to change without notice, and that any information contained within the code should be considered as work in progress.)_

Cloud-native technologies can be applied to Artificial Intelligence (AI) for scalable
application in dynamic environments such as public, private and hybrid cloud. But
it requires cloud native design to decompose monolithic inference pipeline into several
microservices.

![](docs/cnap_arch.png)

The major microservices includes:

| Microservice | Role | Description  |
| ------------ | ---- | ----------- |
| Transcoding Gateway | Data Source | Receive multiple real-time streams and perform transcoding |
| Frame Queue | Data Integration | Assign the input stream into specific work queue |
| Infer Engine | Data Analytics | Infer the frame and send result to result broker |
| Dashboard | Data Visualization | Render the result into client's single page application |