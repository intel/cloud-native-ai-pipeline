#!/bin/bash

set -e

# Define the directory containing the helm charts
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
helm_dir="$script_dir/../helm"

# Automatically detect the helm charts
mapfile -t charts < <(find "$helm_dir" -maxdepth 1 -type d -exec basename {} \; | grep -v "^helm$")

# Function to install a helm chart
install_chart() {
    echo "------------------------------------------"
    echo "INSTALLING CHART: $1"
    echo "------------------------------------------"
    helm install "$1" "$helm_dir"/"$1" || {
        echo "ERROR: Installation of $1 chart failed. Attempting to clean up."
        echo "------------------------------------------"
        helm uninstall "$1" || {
            echo "ERROR: Cleanup of $1 chart also failed."
            echo "------------------------------------------"
        }
        return 1
    }
    echo "SUCCESS: Installation of $1 chart complete."
    echo "------------------------------------------"
}

# Function to uninstall a helm chart
uninstall_chart() {
    local chart=$1
    if is_chart_installed "$chart"; then
        echo "------------------------------------------"
        echo "UNINSTALLING CHART: $chart"
        echo "------------------------------------------"
        helm uninstall "$chart" || {
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
    helm list --deployed --short | grep -q "^$release_name$"
}


# Function to list all available charts
list_charts() {
    echo "------------------------------------------"
    echo "AVAILABLE CHARTS:"
    for chart in "${charts[@]}"; do
        echo "- $chart"
    done
    echo "------------------------------------------"
}

# Function to print help info
print_help() {
    echo "Usage: ./helm-manager.sh [OPTION]... [CHART]..."
    echo ""
    echo "Options:"
    echo "-h          Display this help and exit."
    echo "-l          List all available charts."
    echo "-i          Install specified chart(s), or all charts if no chart is specified."
    echo "-u          Uninstall specified chart(s), or all charts if no chart is specified."
    exit 0
}

# If no arguments are provided, print the help info and exit
if [ $# -eq 0 ]; then
    print_help
fi

# Parse command-line options
while getopts "hliu" opt; do
    case ${opt} in
        h)
            print_help
            ;;
        l)
            list_charts
            ;;
        i)
            install_opt=true
            ;;
        u)
            uninstall_opt=true
            ;;
        \?)
            echo "Invalid option: -${OPTARG}. Use -h for help."
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

# Process remaining arguments (chart names)
for arg in "$@"; do
    if [[ "${charts[*]}" =~ ${arg} ]]; then
        if [[ "${install_opt}" = true ]]; then
            install_chart "${arg}"
        elif [[ "${uninstall_opt}" = true ]]; then
            uninstall_chart "${arg}"
        fi
    else
        echo "Invalid chart name: ${arg}. Use -h for help."
        exit 1
    fi
done

# If no charts specified, install/uninstall all
if [ -z "$1" ]; then
    if [[ "${install_opt}" = true ]]; then
        install_all_charts
    elif [[ "${uninstall_opt}" = true ]]; then
        uninstall_all_charts
    fi
fi
