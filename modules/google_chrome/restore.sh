#!/bin/bash
# $1 is the backup directory passed from the main program
BACKUP_DIR="$1"
CONFIG_DIR="$HOME/.config/google-chrome"

if [ -d "$BACKUP_DIR/config" ]; then
    mkdir -p "$CONFIG_DIR"
    cp -r "$BACKUP_DIR/config/"* "$CONFIG_DIR/"
fi
