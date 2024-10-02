#!/bin/bash

# Директория для бэкапа передается как первый аргумент
BACKUP_DIR="$1"

# Убеждаемся, что директория бэкапа существует
mkdir -p "$BACKUP_DIR"

echo "Бэкап настроек GNOME..."

# Бэкап настроек dconf
dconf dump / > "$BACKUP_DIR/dconf_settings.conf"

echo "Бэкап установленных расширений GNOME..."

EXTENSIONS_DIR="$HOME/.local/share/gnome-shell/extensions"
if [ -d "$EXTENSIONS_DIR" ]; then
    mkdir -p "$BACKUP_DIR/extensions"
    cp -r "$EXTENSIONS_DIR"/* "$BACKUP_DIR/extensions/"
fi

# Бэкап списка установленных расширений через gnome-extensions
if command -v gnome-extensions >/dev/null 2>&1; then
    gnome-extensions list > "$BACKUP_DIR/extensions_list.txt"
else
    echo "Команда gnome-extensions не найдена. Убедитесь, что пакет gnome-extensions установлен."
fi

# Создаем манифест
cat <<EOF > "$BACKUP_DIR/manifest.yaml"
module_name: gnome_settings
version: 1.0
backup_date: $(date -Iseconds)
EOF

echo "Бэкап завершен."
