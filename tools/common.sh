#!/bin/bash

####################################################################################
# This function is used to download a file from a given URL, but only if the file
# does not already exist with the correct MD5 hash. If the file does exist but the
# MD5 hash is different, the existing file is deleted and a new one is downloaded.
#
# Usage: download_file [file_path] [download_url] [expected_md5]
#
# Parameters:
#   file_path:     The path where the file should be saved.
#   download_url:  The URL from which the file should be downloaded.
#   expected_md5:  The expected MD5 hash of the file. If the file already exists
#                  and its MD5 hash matches this value, the file will not be 
#                  downloaded again.
#
# Returns:
#   This function returns 1 and prints an error message in two cases:
#     - If the required parameters are not provided.
#     - If the required commands (wget and md5sum) are not available.
#   If the function completes successfully, it does not return any value.
####################################################################################

download_file() {
    # Check if the required parameters are provided
    if [[ $# -ne 3 ]]; then
        printf "Usage: download_file [file_path] [download_url] [expected_md5]\n"
        return 1
    fi

    local file_path="$1"
    local download_url="$2"
    local expected_md5="$3"
    
    # Check if wget and md5sum commands are available
    if ! command -v wget > /dev/null || ! command -v md5sum > /dev/null; then
        printf "wget and md5sum commands are required.\n"
        return 1
    fi

    local need_download=1

    # Check if the file already exists
    if [[ -f $file_path ]]; then
        local md5sum
        md5sum=$(md5sum "$file_path" | grep --only-matching -m 1 '^[0-9a-f]*')
        
        # If the MD5SUM of the existing file matches the expected MD5, no need to download the file
        if [[ "$md5sum" == "$expected_md5" ]]; then
            need_download=0
        else
            printf "MD5SUM mismatch. Deleting the existing file.\n"
            if ! rm "$file_path"; then
                printf "Failed to delete the existing file. Please check the file permissions.\n"
                return 1
            fi
        fi
    fi

    # Download the file if needed
    if ((need_download)); then
        if wget -O "$file_path" --show-progress "$download_url"; then
            local new_md5sum
            new_md5sum=$(md5sum "$file_path" | grep --only-matching -m 1 '^[0-9a-f]*')
            if [[ "$new_md5sum" == "$expected_md5" ]]; then
                printf "Success download %s\n" "$file_path"
            else
                printf "MD5SUM mismatch after download. Please check the source file.\n"
                return 1
            fi
        else
            printf "Failed to download the file. Please check the URL and network connection.\n"
            return 1
        fi
    else
        printf "%s already exists.\n" "$file_path"
    fi
}
