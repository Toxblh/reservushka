#!/bin/bash

# Директория с бэкапом передается как первый аргумент
BACKUP_DIR="$1"

echo "Восстановление настроек GNOME..."

# Проверяем, есть ли файл настроек
if [ -f "$BACKUP_DIR/dconf_settings.conf" ]; then
    # Резервируем текущие настройки
    dconf dump / > "$HOME/dconf_settings_backup_$(date +%s).conf"
    
    # Восстанавливаем настройки
    dconf load / < "$BACKUP_DIR/dconf_settings.conf"
else
    echo "Файл dconf_settings.conf не найден в бэкапе."
fi

echo "Восстановление расширений GNOME..."

EXTENSIONS_DIR="$HOME/.local/share/gnome-shell/extensions"

# Восстанавливаем директорию расширений
if [ -d "$BACKUP_DIR/extensions" ]; then
    # Создаем директорию, если она не существует
    mkdir -p "$EXTENSIONS_DIR"
    
    # Копируем расширения
    cp -r "$BACKUP_DIR/extensions/"* "$EXTENSIONS_DIR/"
else
    echo "Директория extensions не найдена в бэкапе."
fi

# Включаем расширения
if [ -f "$BACKUP_DIR/extensions_list.txt" ]; then
    if command -v gnome-extensions >/dev/null 2>&1; then
        while read -r extension; do
            gnome-extensions enable "$extension"
        done < "$BACKUP_DIR/extensions_list.txt"
    else
        echo "Команда gnome-extensions не найдена. Убедитесь, что пакет gnome-extensions установлен."
    fi
fi

# Перезагружаем GNOME Shell
echo "Перезагрузка GNOME Shell для применения настроек и расширений..."

if [ "$XDG_SESSION_TYPE" = "x11" ]; then
    # Для X11
    echo "Перезагрузка GNOME Shell для X11..."
    DISPLAY=:0 gnome-shell --replace &
elif [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    # Для Wayland
    echo "Перезагрузка GNOME Shell для Wayland..."
    busctl --user call org.gnome.Shell /org/gnome/Shell org.gnome.Shell Eval s 'Meta.restart("Restarting GNOME Shell for settings restore")'
else
    echo "Неизвестный тип сессии: $XDG_SESSION_TYPE"
fi

echo "Восстановление завершено."
