#!/bin/bash
CONFIG_DIR="$HOME/.config/google-chrome"
if [ -d "$CONFIG_DIR" ]; then
    cd "$CONFIG_DIR"
    for dir in *; do
        if [ -d "$dir" ] && [[ "$dir" == "Profile "* || "$dir" == "Default" ]]; then
            echo "$dir"
        fi
    done
fi
