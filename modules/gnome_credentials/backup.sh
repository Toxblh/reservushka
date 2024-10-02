#!/bin/bash

# Директория для бэкапа передается как первый аргумент
BACKUP_DIR="$1"

# Убеждаемся, что директория бэкапа существует
mkdir -p "$BACKUP_DIR"

echo "Бэкап GNOME Online Accounts..."
# Бэкап настроек GOA
dconf dump /org/gnome/online-accounts/ > "$BACKUP_DIR/goa.conf"

echo "Бэкап GNOME Keyring..."
# Бэкап GNOME Keyring
KEYRING_DIR="$HOME/.local/share/keyrings"
if [ -d "$KEYRING_DIR" ]; then
    cp -r "$KEYRING_DIR" "$BACKUP_DIR/keyrings"
fi

# Создаем манифест
cat <<EOF > "$BACKUP_DIR/manifest.yaml"
module_name: gnome_credentials
version: 1.0
backup_date: $(date -Iseconds)
EOF

echo "Бэкап завершен."
