#!/bin/bash

###############################################################################
# This script downloads sample videos from a GitHub repository and saves them
# in the <top_dir>/sample-videos directory.
#
# The videos are licensed under the Attribution 4.0 license and can be found at
# https://github.com/intel-iot-devkit/sample-videos/
###############################################################################

current_directory=$(readlink -f "$(dirname "${BASH_SOURCE[0]}")")
top_directory=$(dirname "$current_directory")

# Check if common.sh file exists
if [[ ! -f "${current_directory}/common.sh" ]]; then
    printf "common.sh file not found.\n"
    exit 1
fi

source "${current_directory}/common.sh"

# Create a cache directory if it doesn't exist
mkdir -p "${top_directory}/.cache"
cd "${top_directory}/.cache" || exit 1

# Check if unzip command is available
if ! command -v unzip > /dev/null; then
    printf "unzip command is required.\n"
    exit 1
fi

# Download the sample videos
if ! download_file sample-videos.zip \
    https://github.com/intel-iot-devkit/sample-videos/archive/b8e3425998213e0b4957c20f0ed5f83411f7a802.zip \
    22d5c4974d7d6407a470958be5ecfe9a; then
    printf "Failed to download the sample videos.\n"
    exit 1
fi

# Unzip the sample videos if the directory doesn't exist
if [[ ! -d ${top_directory}/.cache/sample-videos-b8e3425998213e0b4957c20f0ed5f83411f7a802 ]]; then
    if ! unzip sample-videos.zip; then
        printf "Failed to unzip the sample videos.\n"
        exit 1
    fi
fi

# Copy the sample videos to the sample-videos directory
if [[ ! -d ${top_directory}/sample-videos ]]; then
    mkdir -p "${top_directory}/sample-videos"
    if ! cp --recursive "${top_directory}/.cache/sample-videos-b8e3425998213e0b4957c20f0ed5f83411f7a802/"* "${top_directory}/sample-videos/"; then
        printf "Failed to copy the sample videos.\n"
        exit 1
    fi
fi

printf "Success\n"

# Clean up
if ! rm -rf "${top_directory}/.cache/sample-videos-b8e3425998213e0b4957c20f0ed5f83411f7a802"; then
    printf "Failed to clean up the temporary directory.\n"
    exit 1
fi
