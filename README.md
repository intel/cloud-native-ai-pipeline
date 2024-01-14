# Cloud Native AI Pipeline

![CI Check License](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-license-check.yaml/badge.svg)
![CI Check Spelling](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-doclint.yaml/badge.svg)
![CI Check Python](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-python-check.yaml/badge.svg)
![CI Check Shell](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-shell-check.yaml/badge.svg)
![CI Check Node](https://github.com/intel/cloud-native-ai-pipeline/actions/workflows/pr-node-check.yaml/badge.svg)

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

## 2. Uses

It is extended for the following uses:

- `End-to-End Macro Bench Framework` for cloud native pipeline like DeathStar Bench
- `Trusted AI pipeline` to protect input stream or model in TEE VM/Container
- `Sustainable AI computing` to reduce carbon footprint for AI workloads

For the details of how to use Trust Execution Environment (TEE) to enhance the security of AI model, please refer
[How to Protect AI Models in Cloud-Native Environments](docs/How_to_Protect_AI_Models_in_Cloud_Native_Environments.md)

![](docs/cnap-uses.png)

## 3. Building

The provided [build script](tools/docker_image_manager.sh) simplifies the process of building Docker images for our microservices. For instance, to build all Docker images, use the following command:

```bash
./tools/docker_image_manager.sh -a build -r <your-registry>
```

The `-a` argument specifies the action(either `build`, `publish`, `save` or `all`), and `-r` is the prefix string for your docker registry

You can get more detail options and arguments for `docker_image_manager.sh` via `./tools/docker_image_manager.sh -h`

The Dockerfile is under the directories in [container](container/)

## 4. Deployment

Before you deploy the helm chart, you need to setup the kubernetes cluster and install the helm tool. Please refer to the [kubernetes documentation](https://kubernetes.io/docs/setup/) and [helm documentation](https://helm.sh/docs/intro/install/) for more details. We also deliver a quick start script to setup the kubernetes cluster:

```bash
# This is a quick start script for ubuntu
bash ./tools/prerequisites/k8s-setup.sh
```

We deliver the helm chart for deployment. After you **finish** building the images and upload to your registry, you need to update the helm chart values `image.repository` to your registry and `image.tag` to your build tag, which defined in each helm chart. Then, assume you navigate to the project's root directory, you can use the following options to install the helm chart:

### Deploy with the helm manager

1. Navigate to the project's root directory.

2. Execute the Helm manager script with the appropriate arguments. For instance, to install all Helm charts, use the following command:

   ```bash
   ./tools/helm_manager.sh -i
   # To uninstall all charts
   # ./tools/helm_manager.sh -u
   ```

   The `-i` argument triggers the installation of Helm charts.

   You can also specify a specific chart to install or uninstall using the chart name as an argument. For instance:

   ```bash
   ./tools/helm_manager.sh -i <chart_name>
   ./tools/helm_manager.sh -u <chart_name>
   ```

   Use `-l` to list all available charts and `-h` to display help information.

Please refer to the [script](./tools/helm_manager.sh) source code for more detailed information on how they work and the full range of available options.

### Deploy with the helm command

1. Navigate to the project's root directory.

2. Execute the Helm manager script with the appropriate arguments. For instance, to install all Helm charts, use the following command:

    ```bash
    # helm install <customer-release-name> <helm-chart-directory>

    # Redis service
    helm install redis ./helm/redis
    # Optional, if you want to see the redis dashboard in grafana: helm install redis-exporter ./helm/redis-exporter

    # Inference service
    helm install inference ./helm/inference

    # SPA service
    helm install pipelineapi ./helm/pipelineapi
    helm install websocket ./helm/websocket
    helm install ui ./helm/ui

    # Steam service
    helm install stream ./helm/stream
    ```

The dashboard of CNAP will be available at `http://<your-ip>:31002`, it is exposed as a NodePort service in kubernetes.

**Note**: This is pre-release/prototype software and, as such, it may be substantially modified as updated versions are made available.

## 5. Integration

The Cloud Native AI Pipeline incorporates several key technologies to foster a robust, scalable, and insightful environment conducive for cloud-native deployments. Our integration encompasses monitoring, visualization, and event-driven autoscaling to ensure optimized performance and efficient resource utilization.

### Monitoring with Prometheus

Our project is instrumented to expose essential metrics to [Prometheus](https://prometheus.io/), a reliable monitoring solution that aggregates and stores metric data. This metric exposition forms the basis for informed autoscaling decisions, ensuring our system dynamically adapts to workload demands. 

Note that, when you want to deploy the workloads into other namespace, please first patch the Prometheus RoleBinding to grant the permission to access the workloads in other namespace:

```bash
kubectl apply -f ./k8s-manifests/prometheus/ClusterRole-All.yaml
```

### Visualization with Grafana

[Grafana](https://grafana.com/) is employed to provide visual insights into the system's performance and the efficacy of the autoscaling integration. Through intuitive dashboards, we can monitor and analyze the metrics collected by Prometheus, fostering a transparent and insightful monitoring framework.

The dashboards of this project is available at `./k8s-manifests/grafana/dashboards`, you can import it into your grafana.

### Event-Driven Autoscaling with KEDA

[Kubernetes Event-driven Autoscaling (KEDA)](https://keda.sh/) is integrated as an operator to orchestrate the dynamic scaling of our Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA) based on the metrics collected by Prometheus. This synergy ensures that resources are efficiently allocated in real-time, aligning with the fluctuating workload demands, thus embodying the essence of cloud-native scalability.

As our project evolves, we envisage the integration of additional technologies to further enhance the cloud-native capabilities of our AI pipeline. For a deeper dive into the current integration and instructions on configuration and usage, refer to the [Integration Documentation](./docs/KEDA.md).

To integrate KEDA with Prometheus, you need to deploy the Service Monitor CR for KEDA:

```bash
kubectl apply -f ./k8s-manifests/keda/keda-service-monitor.yaml
```

And an example of KEDA ScaledObject is available at `./k8s-manifests/keda/infer_scale.yaml`, you can deploy it to your kubernetes cluster to scale the workloads.

### Sustainability with Kepler

In our endeavor to not only optimize the performance but also minimize the environmental impact of our Cloud Native AI Pipeline, we have integrated [Kepler](https://github.com/sustainable-computing-io/kepler), a Kubernetes-based Efficient Power Level Exporter. Kepler employs eBPF to probe system statistics and utilizes machine learning models to estimate the energy consumption of workloads based on these statistics. The energy consumption metrics are then exported to Prometheus, enriching our monitoring framework with vital data that reflects the energy efficiency of our deployments.

This integration aligns with our sustainability objectives by providing a clear insight into the energy footprint of our workloads. By understanding and analyzing the energy metrics provided by Kepler, we can make informed decisions to optimize the energy efficiency of our pipeline, thus contributing to a more sustainable and eco-friendly cloud-native environment.

Furthermore, the integration of Kepler augments our existing monitoring setup with Prometheus and visualization through Grafana, by extending the metrics collection to include energy consumption metrics. This not only enhances our monitoring and visualization framework but also fosters a more holistic understanding of our system's performance and its environmental impact.

For more details on configuring and utilizing Kepler for energy efficiency monitoring, refer to the [Kepler Documentation](https://sustainable-computing.io/).

## 6. Contributors

<!-- spell-checker: disable -->

<!-- readme: contributors -start -->
<table>
<tr>
    <td align="center">
        <a href="https://github.com/leyao-daily">
            <img src="https://avatars.githubusercontent.com/u/54387247?v=4" width="100;" alt="leyao-daily"/>
            <br />
            <sub><b>Le Yao</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/Hulongyin">
            <img src="https://avatars.githubusercontent.com/u/108726629?v=4" width="100;" alt="Hulongyin"/>
            <br />
            <sub><b>Longyin Hu</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/kenplusplus">
            <img src="https://avatars.githubusercontent.com/u/31843217?v=4" width="100;" alt="kenplusplus"/>
            <br />
            <sub><b>Lu Ken</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/dongx1x">
            <img src="https://avatars.githubusercontent.com/u/34326010?v=4" width="100;" alt="dongx1x"/>
            <br />
            <sub><b>Xiaocheng Dong</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/Yanbo0101">
            <img src="https://avatars.githubusercontent.com/u/110962880?v=4" width="100;" alt="Yanbo0101"/>
            <br />
            <sub><b>Yanbo Xu</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/hwang37">
            <img src="https://avatars.githubusercontent.com/u/36193324?v=4" width="100;" alt="hwang37"/>
            <br />
            <sub><b>Wang, Hongbo</b></sub>
        </a>
    </td></tr>
<tr>
    <td align="center">
        <a href="https://github.com/pingzhaozz">
            <img src="https://avatars.githubusercontent.com/u/56963659?v=4" width="100;" alt="pingzhaozz"/>
            <br />
            <sub><b>Null</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/jialeif">
            <img src="https://avatars.githubusercontent.com/u/88661406?v=4" width="100;" alt="jialeif"/>
            <br />
            <sub><b>Jialei Feng</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/rdower">
            <img src="https://avatars.githubusercontent.com/u/15023397?v=4" width="100;" alt="rdower"/>
            <br />
            <sub><b>Robert Dower</b></sub>
        </a>
    </td></tr>
</table>
<!-- readme: contributors -end -->

<!-- spell-checker: enable -->
