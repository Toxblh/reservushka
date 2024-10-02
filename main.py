import os
import sys
import time
import shutil
import datetime
import yaml
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ftplib import FTP
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image, ImageTk

# Global variables
MODULES_DIR = 'modules'
BACKUP_DIR = 'backup_temp'
BACKUP_ARCHIVE = 'backup_archive.zip'

class Module:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.load_config()
        self.data_found = False
        self.profiles = []

    def load_config(self):
        config_files = [f for f in os.listdir(self.path) if f.startswith('module.') and f.split('.')[-1] in ['yaml', 'yml']]
        if not config_files:
            raise Exception(f"No config file found in module {self.name}")
        config_path = os.path.join(self.path, config_files[0])
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.version = self.config.get('version', '1.0')
        self.icon = os.path.join(self.path, self.config.get('icon', 'icon.png'))
        self.backup_paths = self.config.get('backup_paths', [])
        self.profiles_script = self.config.get('profiles_script')
        self.backup_script = self.config.get('backup_script')
        self.restore_script = self.config.get('restore_script')

    def detect_data(self):
        for path in self.backup_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                self.data_found = True
                break

    def detect_profiles(self):
        if self.profiles_script:
            script_path = os.path.join(self.path, self.profiles_script)
            output = os.popen(f'bash "{script_path}"').read()
            self.profiles = output.strip().split('\n')
        else:
            self.profiles = []

class ModuleManager:
    def __init__(self):
        self.modules = {}
        self.load_modules()

    def load_modules(self):
        self.modules.clear()
        if not os.path.exists(MODULES_DIR):
            return
        for module_name in os.listdir(MODULES_DIR):
            module_path = os.path.join(MODULES_DIR, module_name)
            if os.path.isdir(module_path):
                try:
                    module = Module(module_name, module_path)
                    module.detect_data()
                    module.detect_profiles()
                    self.modules[module_name] = module
                except Exception as e:
                    print(f"Error loading module {module_name}: {e}")

class BackupService:
    def __init__(self):
        self.module_manager = ModuleManager()
        self.setup_ui()
        self.start_observer()

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Modular Backup Service")
        self.create_widgets()
        self.populate_modules()

    def create_widgets(self):
        self.module_frame = ttk.Frame(self.root)
        self.module_frame.pack(fill=tk.BOTH, expand=True)

        self.backup_button = ttk.Button(self.root, text="Backup", command=self.backup_selected_modules)
        self.backup_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.restore_button = ttk.Button(self.root, text="Restore", command=self.restore_backup)
        self.restore_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.refresh_button = ttk.Button(self.root, text="Refresh Modules", command=self.refresh_modules)
        self.refresh_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
    def resize_image_proportionally(self, image, max_size):
        # Вычисляем коэффициент масштабирования
        original_width, original_height = image.size
        ratio = min(max_size[0] / original_width, max_size[1] / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Изменяем размер изображения
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)

        # Создаем новое изображение с нужным размером и прозрачным фоном
        new_image = Image.new("RGBA", max_size, (255, 255, 255, 0))

        # Вычисляем позицию для вставки изображения, чтобы оно было по центру
        paste_x = (max_size[0] - new_width) // 2
        paste_y = (max_size[1] - new_height) // 2

        # Вставляем измененное изображение на новое изображение
        new_image.paste(resized_image, (paste_x, paste_y), resized_image.convert("RGBA"))

        return new_image


    def populate_modules(self):
        for widget in self.module_frame.winfo_children():
            widget.destroy()

        self.module_vars = {}
        self.module_images = {}  # Словарь для хранения изображений
        row = 0
        for module_name in sorted(self.module_manager.modules.keys()):
            module = self.module_manager.modules[module_name]
            var = tk.BooleanVar()

            # Загружаем иконку, если она есть
            icon_path = module.icon
            if os.path.exists(icon_path):
                try:
                    image = Image.open(icon_path)
                    # Пропорционально изменяем размер изображения
                    image = self.resize_image_proportionally(image, (32, 32))
                    photo = ImageTk.PhotoImage(image)
                    self.module_images[module_name] = photo  # Сохраняем ссылку на изображение
                    icon_label = tk.Label(self.module_frame, image=photo)
                    icon_label.grid(row=row, column=0, padx=5, pady=2)
                except Exception as e:
                    print(f"Ошибка загрузки иконки для модуля {module_name}: {e}")
                    self.module_images[module_name] = None
                    # Пустой Label для выравнивания
                    icon_label = tk.Label(self.module_frame, width=32, height=32)
                    icon_label.grid(row=row, column=0, padx=5, pady=2)
            else:
                self.module_images[module_name] = None
                # Пустой Label для выравнивания
                icon_label = tk.Label(self.module_frame, width=32, height=32)
                icon_label.grid(row=row, column=0, padx=5, pady=2)

            # Создаем Checkbutton для модуля
            chk = ttk.Checkbutton(self.module_frame, text=module.config.get('name', module_name), variable=var)
            chk.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            self.module_vars[module_name] = var

            # Отображаем статус наличия данных
            status = "Данные найдены" if module.data_found else "Данные не найдены"
            status_label = ttk.Label(self.module_frame, text=status)
            status_label.grid(row=row, column=2, sticky=tk.E, padx=5)
            row += 1


    def refresh_modules(self):
        self.module_manager.load_modules()
        self.populate_modules()

    def backup_selected_modules(self):
        selected_modules = [name for name, var in self.module_vars.items() if var.get()]
        if not selected_modules:
            messagebox.showwarning("No Modules Selected", "Please select at least one module to backup.")
            return
        backup_path = filedialog.askdirectory(title="Select Backup Destination")
        if not backup_path:
            return

        for module_name in selected_modules:
            module = self.module_manager.modules[module_name]
            self.backup_module(module, backup_path)

        # Create backup archive
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        archive_name = os.path.join(backup_path, f"backup_{timestamp}")
        shutil.make_archive(archive_name, 'zip', BACKUP_DIR)
        shutil.rmtree(BACKUP_DIR)
        messagebox.showinfo("Backup Complete", f"Backup completed successfully.\nArchive saved at {archive_name}.zip")

    def backup_module(self, module, backup_root):
        backup_dir = os.path.join(BACKUP_DIR, module.name)
        os.makedirs(backup_dir, exist_ok=True)

        if module.backup_script:
            script_path = os.path.join(module.path, module.backup_script)
            os.system(f'bash "{script_path}" "{backup_dir}"')
        else:
            for path in module.backup_paths:
                src_path = os.path.expanduser(path)
                if os.path.exists(src_path):
                    dest_path = os.path.join(backup_dir, os.path.basename(path))
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        shutil.copy2(src_path, dest_path)

        # Handle profiles (unchanged)
        if module.profiles:
            for profile in module.profiles:
                self.backup_profile(module, profile, backup_dir)

        # Create manifest (unchanged)
        manifest = {
            'module_name': module.name,
            'version': module.version,
            'backup_date': datetime.datetime.now().isoformat(),
            'paths': module.backup_paths,
            'profiles': module.profiles
        }
        with open(os.path.join(backup_dir, 'manifest.yaml'), 'w') as f:
            yaml.dump(manifest, f)

    def backup_profile(self, module, profile, backup_dir):
        profile_backup_dir = os.path.join(backup_dir, 'profiles', profile)
        os.makedirs(profile_backup_dir, exist_ok=True)
        # Copy profile data
        profile_path = os.path.expanduser(f"~/.config/{module.name}/{profile}")
        if os.path.exists(profile_path):
            shutil.copytree(profile_path, os.path.join(profile_backup_dir, profile))

    def restore_backup(self):
        # Option to restore from local file or FTP
        restore_option = messagebox.askyesno("Restore Option", "Do you want to restore from an FTP server?\nYes: FTP\nNo: Local file")
        if restore_option:
            backup_file = self.download_from_ftp()
            if not backup_file:
                return
        else:
            backup_file = filedialog.askopenfilename(title="Select Backup Archive", filetypes=[('Zip Files', '*.zip')])
            if not backup_file:
                return

        extract_dir = os.path.join('/tmp', f"restore_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        os.makedirs(extract_dir, exist_ok=True)
        shutil.unpack_archive(backup_file, extract_dir)

        # Read manifest and present options
        manifest_path = os.path.join(extract_dir, os.listdir(extract_dir)[0], 'manifest.yaml')
        if not os.path.exists(manifest_path):
            messagebox.showerror("Invalid Backup", "Manifest file not found in backup.")
            shutil.rmtree(extract_dir)
            return

        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)

        module_name = manifest.get('module_name')
        module = self.module_manager.modules.get(module_name)
        if not module:
            messagebox.showerror("Module Not Found", f"Module {module_name} not found.")
            shutil.rmtree(extract_dir)
            return

        # Ask user which parts to restore
        restore_all = messagebox.askyesno("Restore Data", f"Do you want to restore all data for {module_name}?")
        if restore_all:
            self.restore_module(module, extract_dir)
        else:
            # Present options for partial restore (e.g., specific profiles)
            self.restore_partial_module(module, extract_dir, manifest)

        shutil.rmtree(extract_dir)
        messagebox.showinfo("Restore Complete", "Data restored successfully.")

    def restore_module(self, module, backup_dir):
        module_backup_dir = os.path.join(backup_dir, module.name)
        if module.restore_script:
            script_path = os.path.join(module.path, module.restore_script)
            os.system(f'bash "{script_path}" "{module_backup_dir}"')
        else:
            for path in module.backup_paths:
                dest_path = os.path.expanduser(path)
                backup_data_path = os.path.join(module_backup_dir, os.path.basename(path))
                if os.path.exists(backup_data_path):
                    if os.path.exists(dest_path):
                        overwrite = messagebox.askyesno(
                            "Overwrite Data", f"Data already exists at {dest_path}. Overwrite?"
                        )
                        if overwrite:
                            if os.path.isdir(dest_path):
                                shutil.rmtree(dest_path)
                            else:
                                os.remove(dest_path)
                        else:
                            continue
                    if os.path.isdir(backup_data_path):
                        shutil.copytree(backup_data_path, dest_path)
                    else:
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(backup_data_path, dest_path)
            # Restore profiles (unchanged)
            profiles_dir = os.path.join(module_backup_dir, 'profiles')
            if os.path.exists(profiles_dir):
                for profile_name in os.listdir(profiles_dir):
                    profile_backup_path = os.path.join(profiles_dir, profile_name)
                    profile_dest_path = os.path.expanduser(f"~/.config/{module.name}/{profile_name}")
                    if os.path.exists(profile_dest_path):
                        overwrite = messagebox.askyesno(
                            "Overwrite Profile", f"Profile {profile_name} already exists. Overwrite?"
                        )
                        if overwrite:
                            shutil.rmtree(profile_dest_path)
                            shutil.copytree(profile_backup_path, profile_dest_path)
                    else:
                        shutil.copytree(profile_backup_path, profile_dest_path)


    def restore_partial_module(self, module, backup_dir, manifest):
        # Implement UI to select specific parts to restore
        # For simplicity, let's assume we only handle profiles here
        profiles = manifest.get('profiles', [])
        if not profiles:
            messagebox.showinfo("No Profiles", "No profiles found in backup.")
            return

        # Create a selection window
        top = tk.Toplevel(self.root)
        top.title(f"Select Profiles to Restore for {module.name}")

        profile_vars = {}
        for idx, profile in enumerate(profiles):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(top, text=profile, variable=var)
            chk.grid(row=idx, column=0, sticky=tk.W, padx=5, pady=2)
            profile_vars[profile] = var

        def on_restore():
            selected_profiles = [p for p, v in profile_vars.items() if v.get()]
            if not selected_profiles:
                messagebox.showwarning("No Profiles Selected", "Please select at least one profile to restore.")
                return
            # Restore selected profiles
            module_backup_dir = os.path.join(backup_dir, module.name)
            profiles_dir = os.path.join(module_backup_dir, 'profiles')
            for profile_name in selected_profiles:
                profile_backup_path = os.path.join(profiles_dir, profile_name)
                profile_dest_path = os.path.expanduser(f"~/.config/{module.name}/{profile_name}")
                if os.path.exists(profile_dest_path):
                    overwrite = messagebox.askyesno("Overwrite Profile", f"Profile {profile_name} already exists. Overwrite?")
                    if overwrite:
                        shutil.rmtree(profile_dest_path)
                        shutil.copytree(profile_backup_path, profile_dest_path)
                else:
                    shutil.copytree(profile_backup_path, profile_dest_path)
            top.destroy()
            messagebox.showinfo("Restore Complete", "Selected profiles restored successfully.")

        restore_button = ttk.Button(top, text="Restore Selected Profiles", command=on_restore)
        restore_button.grid(row=len(profiles), column=0, padx=5, pady=5)

    def start_observer(self):
        event_handler = ModuleEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=MODULES_DIR, recursive=True)
        self.observer.start()

    def run(self):
        self.root.mainloop()
        self.observer.stop()
        self.observer.join()

    # FTP Functions
    def download_from_ftp(self):
        ftp_details = self.get_ftp_details()
        if not ftp_details:
            return None
        ftp_server, ftp_user, ftp_password, remote_file = ftp_details
        local_file_path = os.path.join('/tmp', f"ftp_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.zip")

        try:
            with FTP(ftp_server) as ftp:
                ftp.login(user=ftp_user, passwd=ftp_password)
                with open(local_file_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {remote_file}', f.write)
            return local_file_path
        except Exception as e:
            messagebox.showerror("FTP Error", f"Failed to download backup from FTP: {e}")
            return None

    def get_ftp_details(self):
        # Simple dialog to get FTP details
        ftp_window = tk.Toplevel(self.root)
        ftp_window.title("FTP Details")

        tk.Label(ftp_window, text="FTP Server:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(ftp_window, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(ftp_window, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Label(ftp_window, text="Remote File:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)

        server_entry = tk.Entry(ftp_window)
        user_entry = tk.Entry(ftp_window)
        password_entry = tk.Entry(ftp_window, show="*")
        file_entry = tk.Entry(ftp_window)

        server_entry.grid(row=0, column=1, padx=5, pady=2)
        user_entry.grid(row=1, column=1, padx=5, pady=2)
        password_entry.grid(row=2, column=1, padx=5, pady=2)
        file_entry.grid(row=3, column=1, padx=5, pady=2)

        ftp_details = {}

        def on_submit():
            ftp_details['server'] = server_entry.get()
            ftp_details['user'] = user_entry.get()
            ftp_details['password'] = password_entry.get()
            ftp_details['file'] = file_entry.get()
            ftp_window.destroy()

        submit_button = ttk.Button(ftp_window, text="Download", command=on_submit)
        submit_button.grid(row=4, column=0, columnspan=2, pady=5)

        self.root.wait_window(ftp_window)

        if 'server' in ftp_details:
            return ftp_details['server'], ftp_details['user'], ftp_details['password'], ftp_details['file']
        else:
            return None

class ModuleEventHandler(FileSystemEventHandler):
    def __init__(self, backup_service):
        self.backup_service = backup_service

    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in ['.yaml', '.yml', '.sh']):
            self.backup_service.refresh_modules()

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        self.on_modified(event)

if __name__ == '__main__':
    backup_service = BackupService()
    backup_service.run()
