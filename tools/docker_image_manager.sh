#!/bin/bash

set -e

current_directory=$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")
top_directory=$(dirname "${current_directory}")
container_directory="${top_directory}/container"
action="all"
registry=""
container="all"
tag="latest"
docker_build_clean_param=""
all_containers=()

function scan_all_containers {
    mapfile -t dirs < <(cd "${container_directory}" && ls -d ./*/)
    for dir in "${dirs[@]}"
    do
        dir=${dir#./}
        all_containers+=("${dir::-1}")
    done
}

function usage {
    cat << EOM
usage: $(basename "$0") [OPTION]...
    -a <build|download|publish|save|all>  all is default, which not include save. Please execute save explicity if need.
    -r <registry prefix> the prefix string for registry
    -c <container name> same as directory name
    -g <tag> container image tag
    -f Clean build
EOM
    exit 1
}

function process_args {
while getopts ":a:r:c:g:hf" option; do
        case "${option}" in
            a) action=${OPTARG};;
            r) registry=${OPTARG};;
            c) container=${OPTARG};;
            g) tag=${OPTARG};;
            h) usage;;
            f) docker_build_clean_param="--no-cache --rm";;
            *) echo "Invalid option: -${OPTARG}" >&2
               usage
               ;;
        esac
    done

    if [[ ! "$action" =~ ^(build|download|publish|save|all)$ ]]; then
        echo "invalid type: $action"
        usage
    fi

    if [[ "$container" != "all" ]]; then
        if [[ ! "${all_containers[*]}" =~ ${container} ]]; then
            echo "invalid container name: $container"
            usage
        fi
    fi

    if [[ -z "$registry" ]]; then
        if [[ -z "$EIP_REGISTRY" ]]; then
            echo "Error: Please specify your docker registry via -r <registry prefix> or set environment variable EIP_REGISTRY."
            exit 1
        else
            registry=$EIP_REGISTRY
        fi
    fi
}

function build_a_image {
    local img_container=$1
    echo "Build container image => ${registry}/${img_container}:${tag}"

    if [ -f "${container_directory}/${img_container}/pre-build.sh" ]; then
        echo "Execute pre build script at ${container_directory}/${img_container}/pre-build.sh"
        "${container_directory}/${img_container}/pre-build.sh" || { echo 'Fail to execute pre-build.sh'; exit 1; }
    fi

    docker_build_args=(
        "--build-arg" "http_proxy"
        "--build-arg" "https_proxy"
        "--build-arg" "no_proxy"
        "--build-arg" "pip_mirror"
        "-f" "${container_directory}/${img_container}/Dockerfile"
        "${top_directory}"
        "--tag" "${registry}/${img_container}:${tag}"
    )

    if [[ -n "${docker_build_clean_param}" ]]; then
        read -ar split_params <<< "${docker_build_clean_param}"
        docker_build_args+=("${split_params[@]}")
    fi

    docker build "${docker_build_args[@]}" || \
        { echo "Fail to build docker ${registry}/${img_container}:${tag}"; exit 1; }

    echo "Complete build image => ${registry}/${img_container}:${tag}"

    if [ -f "${container_directory}/${img_container}/post-build.sh" ]; then
        echo "Execute post build script at ${container_directory}/${img_container}/post-build.sh"
        "${container_directory}/${img_container}/post-build.sh" || { echo "Fail to execute post-build.sh"; exit 1; }
    fi

    echo -e "\n\n"
}

function build_images {
    if [[ "$container" == "all" ]]; then
        for img_container in "${all_containers[@]}"
        do
            build_a_image "$img_container"
        done
    else
        build_a_image "$container"
    fi
}

function publish_a_image {
    local img_container=$1
    echo "Publish container image: ${registry}/${img_container}:${tag} ..."
    docker push "${registry}/${img_container}:${tag}" || \
        { echo "Fail to push docker ${registry}/${img_container}:${tag}"; exit 1; }
    echo -e "Complete publish container image ${registry}/${img_container}:${tag} ...\n"
}

function publish_images {
    if [[ "$container" == "all" ]]; then
        for img_container in "${all_containers[@]}"
        do
            publish_a_image "$img_container"
        done
    else
        publish_a_image "$container"
    fi
}

function download_a_image {
    local img_container=$1
    echo "Download container image: ${registry}/${img_container}:${tag} ..."
    crictl pull "${registry}/${img_container}:${tag}" || \
        { echo "Fail to download images ${registry}/${img_container}:${tag}"; exit 1; }
    echo -e "Complete download container image ${registry}/${img_container}:${tag} ...\n"
}

function download_images {
    if [[ "$container" == "all" ]]; then
        for img_container in "${all_containers[@]}"
        do
	    download_a_image "$img_container"
        done
    else
	download_a_image "$container"
    fi
}

function save_a_image {
    local img_container=$1
    echo "Save container image ${registry}/${img_container}:${tag} => ${top_directory}/images/ ... "
    mkdir -p "${top_directory}/images/"
    docker save -o "${top_directory}/images/${img_container}-${tag}.tar" "${registry}/${img_container}:${tag}"
    docker save "${registry}/${img_container}:${tag}" | gzip > "${top_directory}/images/${img_container}-${tag}.tgz"
}

function save_images {
    if [[ "$container" == "all" ]]; then
        for img_container in "${all_containers[@]}"
        do
            save_a_image "$img_container"
        done
    else
        save_a_image "$container"
    fi
}

function check_docker {
    if ! command -v docker &> /dev/null
    then
        echo "Docker could not be found. Please install Docker."
        exit
    fi
}

check_docker
scan_all_containers
process_args "$@"

echo ""
echo "-------------------------"
echo "action: ${action}"
echo "container: ${container}"
echo "tag: ${tag}"
echo "registry: ${registry}"
echo "-------------------------"
echo ""

if [[ "$action" =~ ^(build|all)$ ]]; then
    build_images
fi

if [[ "$action" =~ ^(publish|all)$ ]]; then
    publish_images
fi

if [[ "$action" =~ ^(save)$ ]]; then
    save_images
fi

if [[ "$action" =~ ^(download)$ ]]; then
    download_images
fi

