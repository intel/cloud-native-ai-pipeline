# KEDA Integration Documentation

This document delineates the integration of Kubernetes Event-driven Autoscaling (KEDA) within the Cloud Native AI Pipeline, specifically focusing on augmenting the scalability of the Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA) which are imperative for optimizing resource allocation in cloud-native settings.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Resources](#resources)

## Overview

KEDA, acting as an operator, synergizes with the Cloud Native AI Pipeline to bolster the scalability of HPA and VPA, ensuring efficient resource allocation and optimized performance in response to real-time workload demands.

## Installation

### Prerequisites

- Kubernetes cluster
- Helm 3

### Steps

1. Install KEDA using Helm:
   ```bash
   helm repo add kedacore https://kedacore.github.io/charts
   helm repo update
   helm install keda kedacore/keda --namespace keda
   ```

## Configuration

Configure the scalers and triggers in accordance with the project requirements to fine-tune the autoscaling behavior.

1. Define the ScaledObject or ScaledJob custom resource:

   ```yaml
   apiVersion: keda.sh/v1alpha1
   kind: ScaledObject
   metadata:
     name: example-scaledobject
   spec:
     scaleTargetRef:
       name: example-deployment
     triggers:
     - type: example-trigger
       metadata:
         # trigger-specific configuration
   ```

## Usage

Utilize KEDA to orchestrate the autoscaling of HPA and VPA within the project, ensuring real-time scalability in response to workload dynamics.

### Monitor the autoscaling behavior:

   ```bash
   kubectl get hpa
   ```

Or you can just deploy grafana dashboard for KEDA in grafana and directly monitor the autoscaling behavior.

## Resources

- [KEDA Official Documentation](https://keda.sh/docs/)
- Additional resources and references pertinent to the Cloud Native AI Pipeline and KEDA integration.
