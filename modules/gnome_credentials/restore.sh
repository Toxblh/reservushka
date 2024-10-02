#!/bin/bash

# Директория с бэкапом передается как первый аргумент
BACKUP_DIR="$1"

echo "Восстановление GNOME Online Accounts..."
# Восстанавливаем настройки GOA
if [ -f "$BACKUP_DIR/goa.conf" ]; then
    dconf load /org/gnome/online-accounts/ < "$BACKUP_DIR/goa.conf"
else
    echo "Файл goa.conf не найден в бэкапе."
fi

echo "Восстановление GNOME Keyring..."
# Восстанавливаем GNOME Keyring
KEYRING_DIR="$HOME/.local/share/keyrings"
if [ -d "$BACKUP_DIR/keyrings" ]; then
    # Резервируем существующие ключи, если они есть
    if [ -d "$KEYRING_DIR" ]; then
        mv "$KEYRING_DIR" "${KEYRING_DIR}_backup_$(date +%s)"
    fi
    cp -r "$BACKUP_DIR/keyrings" "$KEYRING_DIR"
else
    echo "Директория keyrings не найдена в бэкапе."
fi

echo "Восстановление завершено."
