#!/bin/bash

# Директория для бэкапа передается как первый аргумент
BACKUP_DIR="$1"

# Убеждаемся, что директория бэкапа существует
mkdir -p "$BACKUP_DIR"

echo "Бэкап Telegram Desktop..."

# Путь к данным Telegram Desktop
TELEGRAM_DIR="$HOME/.local/share/TelegramDesktop"

if [ -d "$TELEGRAM_DIR" ]; then
    cp -r "$TELEGRAM_DIR" "$BACKUP_DIR/TelegramDesktop"
    echo "Данные Telegram Desktop успешно скопированы."
else
    echo "Директория Telegram Desktop не найдена: $TELEGRAM_DIR"
fi

# Создаем манифест
cat <<EOF > "$BACKUP_DIR/manifest.yaml"
module_name: telegram
version: 1.0
backup_date: $(date -Iseconds)
EOF

echo "Бэкап завершен."
