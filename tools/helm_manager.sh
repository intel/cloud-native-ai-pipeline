#!/bin/bash

set -e

# Define the configurations
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
helm_dir="$script_dir/../helm"
repository_url=""
image_tag=""
namespace="default"

# Automatically detect the helm charts
mapfile -t charts < <(find "$helm_dir" -maxdepth 1 -type d -exec basename {} \; | grep -v "^helm$")

# Function to install a helm chart
install_chart() {
    local chart_name=$1
    local helm_args=()

    # Check if repository and tag values are set
    [[ -n "$repository_url" ]] && helm_args+=("--set" "image.repository=$repository_url")
    [[ -n "$image_tag" ]] && helm_args+=("--set" "image.tag=$image_tag")
    [[ -n "$namespace" ]] && helm_args+=("--namespace" "$namespace")

    echo "------------------------------------------"
    echo "INSTALLING CHART: $chart_name"
    echo "------------------------------------------"
    helm install "$chart_name" "$helm_dir"/"$chart_name" "${helm_args[@]}" || {
        echo "ERROR: Installation of $1 chart failed. Attempting to clean up."
        echo "------------------------------------------"
        helm uninstall "$chart_name" || {
            echo "ERROR: Cleanup of $chart_name chart also failed."
            echo "------------------------------------------"
        }
        return 1
    }
    echo "SUCCESS: Installation of $chart_name chart complete."
    echo "------------------------------------------"
}

# Function to uninstall a helm chart
uninstall_chart() {
    local chart=$1
    if is_chart_installed "$chart"; then
        [[ -n "$namespace" ]] && helm_args+=("--namespace" "$namespace")
        echo "------------------------------------------"
        echo "UNINSTALLING CHART: $chart"
        echo "------------------------------------------"
        helm uninstall "$chart"  "${helm_args[@]}" || {
            echo "ERROR: Uninstallation of $chart chart failed."
            echo "------------------------------------------"s
        }
        echo "SUCCESS: Uninstallation of $chart chart complete."
        echo "------------------------------------------"
    else
        echo "NOTE: $chart chart is not installed."
    fi
}

# Function to install all helm charts
install_all_charts() {
    local install_failed=false
    for chart in "${charts[@]}"; do
        install_chart "$chart" || {
            echo "Installation of $chart failed. Continuing with next chart."
            install_failed=true
        }
    done
    if [[ "$install_failed" = true ]]; then
        echo "One or more chart installations failed."
        return 1
    fi
}

# Function to uninstall all installed helm charts
uninstall_all_charts() {
    local chart
    for chart in "${charts[@]}"; do
        uninstall_chart "$chart"
    done
}

# Function to check if a helm chart is installed
is_chart_installed() {
    local release_name=$1
    helm list --short -n "$namespace" | grep -q "^$release_name$"
}


# Function to list all available charts
list_charts() {
    echo "------------------------------------------"
    echo "AVAILABLE CHARTS:"
    for chart in "${charts[@]}"; do
        echo "- $chart"
    done
    echo "------------------------------------------"
    exit 0
}

# Function to print help info
print_help() {
    echo "Usage: ./helm-manager.sh [OPTION]... [CHART]..."
    echo ""
    echo "Options:"
    echo "-h          Display this help and exit."
    echo "-l          List all available charts."
    echo "-i          Install specified chart(s), or all charts if no chart is specified."
    echo "            When using -i, you can optionally set the image repository and tag:"
    echo "            -r <repository_url>   Set the image repository (only valid with -i)."
    echo "            -g <image_tag>       Set the image tag (only valid with -i)."
    echo "-u          Uninstall specified chart(s), or all charts if no chart is specified."
    echo "-n          Set the namespace (can be used with both -i and -u)."
    echo ""
    echo "Examples:"
    echo "./helm-manager.sh -i <chart_name>"
    echo "./helm-manager.sh -i -r <repository_url> -g <image_tag>"
    echo "./helm-manager.sh -i <chart_name> -r <repository_url> -g <image_tag>"
    echo "./helm-manager.sh -u <chart_name>"
    echo "./helm-manager.sh -u"
    exit 0
}

# If no arguments are provided, print the help info and exit
if [ $# -eq 0 ]; then
    print_help
fi

install_charts=()
uninstall_charts=()

# Process all arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h)
            print_help
            ;;
        -l)
            list_charts
            ;;
        -i)
            install_opt=true
            shift
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                install_charts+=("$1")
                shift
            done
            ;;
        -u)
            uninstall_opt=true
            shift
            while [[ $# -gt 0 && ! $1 =~ ^- ]]; do
                uninstall_charts+=("$1")
                shift
            done
            ;;
        -r)
            if [[ "$install_opt" = true ]]; then
                repository_url=$2
                shift 2
            else
                echo "Error: -r option is only valid when -i is set."
                exit 1
            fi
            ;;
        -g)
            if [[ "$install_opt" = true ]]; then
                image_tag=$2
                shift 2
            else
                echo "Error: -g option is only valid when -i is set."
                exit 1
            fi
            ;;
        -n)
            namespace=$2
            shift 2
            ;;
        *)
            echo "Invalid option or chart name: $1. Use -h for help."
            exit 1
            ;;
    esac
done

# Process installation and uninstallation based on the provided charts
if [[ "$install_opt" = true ]]; then
    if [ ${#install_charts[@]} -eq 0 ]; then
        for chart in "${charts[@]}"; do
            install_chart "$chart"
        done
    else
        for chart in "${install_charts[@]}"; do
            install_chart "$chart"
        done
    fi
fi

if [[ "$uninstall_opt" = true ]]; then
    if [ ${#uninstall_charts[@]} -eq 0 ]; then
        uninstall_all_charts
    else
        for chart in "${uninstall_charts[@]}"; do
            uninstall_chart "$chart"
        done
    fi
fi
