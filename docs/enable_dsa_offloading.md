# Redis Memory Operation Offload with DSA

Accelerate memory copy & move operation in Redis with Intel® [DTO](https://github.com/intel/DTO#intel-dsa-transparent-offload-library)(DSA Transparent Offload Library), a shared library for applications to transparently use DSA.

## Prerequisites

Intel® DSA(Data streaming accelerator), [Specification](https://www.intel.com/content/www/us/en/content-details/671116/intel-data-streaming-accelerator-architecture-specification.html?wapkw=data%20streaming%20accelerator%20specification), 
DSA is a high-performance data copy and transformation accelerator that is integrated in 4th Gen Intel(R) Xeon(R) Scalable Processor(Sapphire Rapids) and later.

You need firstly follow DSA [accel-config](https://github.com/intel/idxd-config) to build and install it.

## How to use

### 1. Build Redis & DSA image

You can skip this step if you have already done it before.

```
$ ./tools/docker_image_manager.sh -a build -c cnap-redis -r <your-registry>
```


### 2. Enable DSA in host

Configure DSA:

- Make sure you have installed [accel-config](https://github.com/intel/idxd-config) library and tools before doing this step
```
$ cd k8s-manifests/plugin/dsa/config_dsa
$ ./setup_dsa.sh configs/1e1w-s.conf
```

Run test to verfiy:

- To run dsa_test for single mode, run dsa_test_batch for batch mode
```
$ cd build/bin
$ ./dsa_test -w 0 -l 4096 -o 3
$ ./dsa_test_batch -w 0 -l 4096 -c 16
```

### 3. Setup DSA Device Plugin

The DSA plugin discovers DSA work queues and presents them as a node resources.

```
$ kubectl apply -k k8s-manifests/plugin/dsa/intel-dsa-plugin.yaml
daemonset.apps/intel-dsa-plugin created
```

Verify DSA device plugin:
```
$ kubectl get nodes -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{range $k,$v:=.status.allocatable}}{{"  "}}{{$k}}{{": "}}{{$v}}{{"\n"}}{{end}}{{end}}' | grep '^\([^ ]\)\|\(  dsa\)'
master
  dsa.intel.com/wq-user-shared: 8
node1
  dsa.intel.com/wq-user-shared: 20
```

### 4. Enable Redis offload with DSA

We have integrated Redis offloading with DSA in CNAP, you can modify the helm/redis/values.yaml to enable DSA:

```
dsa:
  enabled: true
  wqnumbers: 2
```

To enable Redis offloading with DSA in other user scenarios, you can update Redis deployment yaml file directly as below:
```
image: <redis_image_build_before_with_DTO>
command: ["/opt/redis/redis-server-dto"]
resources:
  limits:
    dsa.intel.com/wq-user-shared: <wp_numbers_want_to_be_allocated>
```

### 5. Deployment

Same deployment command as original with your image registry

```
$ ./tools/helm_manager.sh -i -r <your-registry> -g <image-tag>
# To uninstall all charts
# ./tools/helm_manager.sh -u
```

