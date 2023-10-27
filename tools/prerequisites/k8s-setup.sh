#!/bin/bash

set -e

execute_command() {
    local command=$1
    local return_output=$2
    local temp_file

    if [[ $return_output -eq 1 ]]; then
        local output
        temp_file=$(mktemp)
        eval "$command" 2>&1 | tee "$temp_file"
        output=$(cat "$temp_file")
        rm -f "$temp_file"
        echo "$output"
    else
        eval "$command" 2>&1
    fi
}

check_host_readiness() {
    # Check if script is run as root
    if [[ $EUID -ne 0 ]]; then
        echo "Please run as root"
        exit 1
    fi

    # Check kernel version (assuming a minimum kernel version of 3.10)
    kernel_version=$(uname -r)
    major_version=$(echo "$kernel_version" | cut -d. -f1)
    minor_version=$(echo "$kernel_version" | cut -d. -f2)
    if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 10 ]]; then
        echo "Kernel version $kernel_version is not supported. Minimum required is 3.10"
        exit 1
    fi
}

disable_swap() {
    commands=(
        "swapoff -a"
        "sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

configure_kernel() {
    commands=(
        "tee /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF"
        "modprobe overlay"
        "modprobe br_netfilter"
        "tee /etc/sysctl.d/kubernetes.conf <<EOF
net.bridge.bridge-nf-call-ip6tables=1
net.bridge.bridge-nf-call-iptables=1
net.ipv4.ip_forward=1
EOF"
        "sysctl --system"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

install_pre_requisites() {
    commands=(
        "apt-get update"
        "apt-get install -y apt-transport-https ca-certificates curl gnupg software-properties-common debian-keyring debian-archive-keyring"
        "mkdir -p -m 755 /etc/apt/keyrings"
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/docker-archive-keyring.gpg --import --batch --yes"
        "chmod 644 /etc/apt/trusted.gpg.d/docker-archive-keyring.gpg"
        "add-apt-repository -y \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\""
        "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg --import --batch --yes"
        "chmod 644 /etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg"
        "apt-add-repository -y \"deb http://apt.kubernetes.io/ kubernetes-xenial main\""
        "apt-get update"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

install_container() {
    commands=(
        "apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

configure_container() {
    commands=(
        "mkdir -p /etc/containerd"
        "containerd config default | tee /etc/containerd/config.toml >/dev/null 2>&1"
        "sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml"
        "systemctl daemon-reload"
        "systemctl restart containerd"
        "systemctl enable containerd"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

install_kubernetes() {
    read -rp "Enter Kubernetes version (default: 1.28.2-00): " k8s_version
    k8s_version=${k8s_version:-"1.28.2-00"}

    commands=(
        "apt-get install -y kubelet=${k8s_version} kubeadm=${k8s_version} kubectl=${k8s_version} --allow-change-held-packages"
        "apt-mark hold kubelet kubeadm kubectl"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

initialize_cluster() {
    read -rp "Enter Pod Network CIDR (default: 10.244.0.0/16): " pod_network_cidr
    pod_network_cidr=${pod_network_cidr:-"10.244.0.0/16"}
    command="kubeadm init --pod-network-cidr=${pod_network_cidr}"
    output=$(execute_command "$command" 1)

    commands=(
        "mkdir -p $HOME/.kube"
        "cp /etc/kubernetes/admin.conf $HOME/.kube/config"
        "chown $(id -u):$(id -g) $HOME/.kube/config"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
    
    join_command=$(echo "$output" | grep -A 1 "kubeadm join" | tr -d \\ | tr -d '\n')
    if [[ -z $join_command ]]; then
        echo "Failed to extract kubeadm join command details."
        return
    fi
    
    master_ip=$(echo "$join_command" | awk '{print $3}' | cut -d':' -f1)
    token=$(echo "$join_command" | awk '{print $5}')
    cert_hash=$(echo "$join_command" | awk '{print $7}')

    echo "Master IP: $master_ip"
    echo "Token: $token"
    echo "Certificate Hash: $cert_hash"
    
    enable_kubectl_autocompletion
    
    echo "Cluster initialized with Pod Network CIDR $pod_network_cidr"
}

join_cluster() {
    read -rp "Enter token to join the cluster: " token
    read -rp "Enter certificate hash: " cert_hash
    read -rp "Enter master node IP address: " master_ip
    command="kubeadm join ${master_ip}:6443 --token $token --discovery-token-ca-cert-hash sha256:$cert_hash"
    execute_command "$command"
}

enable_kubectl_autocompletion() {
    commands=(
        "apt-get install -y bash-completion"
        "echo 'source <(kubectl completion bash)' >> ~/.bashrc"
        "source ~/.bashrc"
    )
    for command in "${commands[@]}"; do
        execute_command "$command"
    done
}

setup_cluster() {
    echo "1: Initialize as Controller Node"
    echo "2: Join as Worker Node"
    read -rp "Enter choice (default: 1): " choice
    choice=${choice:-'1'}

    if [[ $choice == '1' ]]; then
        initialize_cluster
    elif [[ $choice == '2' ]]; then
        join_cluster
    else
        echo "Invalid choice. Exiting."
        exit 1
    fi
}

install_cni() {
    read -rp "Do you want to setup a Container Network Interface (CNI)? Enter 'yes' to setup or 'no' to skip (default: yes): " cni_choice
    cni_choice=${cni_choice:-"yes"}

    if [[ $cni_choice == 'no' ]]; then
        echo "Skipping CNI setup."
        return
    fi
    
    echo "Choose a CNI plugin:"
    echo "1: Calico"
    echo "2: Flannel"
    read -rp "Enter choice (default: 1): " cni_plugin_choice
    cni_plugin_choice=${cni_plugin_choice:-'1'}
    
    if [[ $cni_plugin_choice == '1' ]]; then
        calico_url="https://projectcalico.docs.tigera.io/manifests/calico.yaml"
        command="kubectl apply -f $calico_url"
        execute_command "$command"
        echo "Calico CNI plugin has been installed."
    elif [[ $cni_plugin_choice == '2' ]]; then
        flannel_url="https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml"
        command="kubectl apply -f $flannel_url"
        execute_command "$command"
        echo "Flannel CNI plugin has been installed."
    else
        echo "Invalid choice. Exiting."
        exit 1
    fi
}

main_menu() {

    check_host_readiness

    while true; do
        echo "Choose a step to execute:"
        echo "0: Execute all steps"
        echo "1: disable_swap"
        echo "2: configure_kernel"
        echo "3: install_pre_requisites"
        echo "4: install_container"
        echo "5: configure_container"
        echo "6: install_kubernetes"
        echo "7: setup_cluster"
        echo "8: install_cni"
        echo "9: Exit"
        read -rp "Enter step number: " choice

        case $choice in
            0)
                disable_swap
                configure_kernel
                install_pre_requisites
                install_container
                configure_container
                install_kubernetes
                setup_cluster
                install_cni
                break
                ;;
            1)
                disable_swap
                ;;
            2)
                configure_kernel
                ;;
            3)
                install_pre_requisites
                ;;
            4)
                install_container
                ;;
            5)
                configure_container
                ;;
            6)
                install_kubernetes
                ;;
            7)
                setup_cluster
                ;;
            8)
                install_cni
                ;;
            9)
                break
                ;;
            *)
                echo "Invalid step number. Please try again."
                ;;
        esac
    done
}

main_menu
