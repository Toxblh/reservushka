#!/bin/bash
# $1 is the backup directory passed from the main program
BACKUP_DIR="$1"
CONFIG_DIR="$HOME/.config/google-chrome"

if [ -d "$CONFIG_DIR" ]; then
    mkdir -p "$BACKUP_DIR/config"
    cp -r "$CONFIG_DIR/"* "$BACKUP_DIR/config/"
fi
