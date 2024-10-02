#!/bin/bash

# Директория с бэкапом передается как первый аргумент
BACKUP_DIR="$1"

echo "Восстановление Telegram Desktop..."

# Путь к данным Telegram Desktop
TELEGRAM_DIR="$HOME/.local/share/TelegramDesktop"

# Проверяем наличие бэкапа
if [ -d "$BACKUP_DIR/TelegramDesktop" ]; then
    # Резервируем текущие данные Telegram Desktop, если они существуют
    if [ -d "$TELEGRAM_DIR" ]; then
        mv "$TELEGRAM_DIR" "${TELEGRAM_DIR}_backup_$(date +%s)"
        echo "Существующие данные Telegram Desktop были перемещены в резервную копию."
    fi

    # Восстанавливаем данные из бэкапа
    cp -r "$BACKUP_DIR/TelegramDesktop" "$HOME/.local/share/"
    echo "Данные Telegram Desktop успешно восстановлены."
else
    echo "Бэкап Telegram Desktop не найден в: $BACKUP_DIR/TelegramDesktop"
fi

echo "Восстановление завершено."
