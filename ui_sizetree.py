import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

def get_dir_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                # Abaikan symlink/junction agar tidak terjadi infinite loop atau salah hitung
                if entry.is_symlink():
                    continue
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
            except (PermissionError, FileNotFoundError, OSError):
                # Lewati file/folder yang diproteksi sistem (seperti System Volume Information)
                pass
    except (PermissionError, FileNotFoundError, OSError):
        pass
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class SizeTreeFrame(ctk.CTkFrame):
    def __init__(self, master, navigate_to_create_callback, **kwargs):
        super().__init__(master, **kwargs)
        # Menyimpan fungsi callback untuk melompat ke Menu Create Link
        self.navigate_to_create_callback = navigate_to_create_callback
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Folder Size Analyzer", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=10, pady=(0, 20), sticky="w")

        # Top control frame
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.top_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.top_frame, text="Target Path:").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.entry_path = ctk.CTkEntry(self.top_frame, placeholder_text="e.g. C:\\Users\\Name\\AppData")
        self.entry_path.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self.top_frame, text="Browse", width=80, fg_color="#333333", hover_color="#555555", command=self.browse_folder)
        self.btn_browse.grid(row=0, column=2, padx=5, pady=5)

        self.btn_scan = ctk.CTkButton(self.top_frame, text="Scan", width=80, fg_color="#8B0000", hover_color="#A52A2A", font=ctk.CTkFont(weight="bold"), command=self.start_scan)
        self.btn_scan.grid(row=0, column=3, padx=(5, 0), pady=5)

        # Scrollable Frame untuk hasil
        self.result_scroll = ctk.CTkScrollableFrame(self, fg_color="#2B2B2B")
        self.result_scroll.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Status label di bagian bawah
        self.status_label = ctk.CTkLabel(self, text="Ready. Select a folder and click Scan.", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            folder = os.path.normpath(folder)
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder)

    def start_scan(self):
        target_path = self.entry_path.get().strip()
        if not target_path or not os.path.exists(target_path):
            messagebox.showerror("Error", "Path tidak valid atau folder tidak ditemukan!")
            return

        self.btn_scan.configure(state="disabled")
        self.btn_browse.configure(state="disabled")
        
        # Bersihkan hasil sebelumnya
        for widget in self.result_scroll.winfo_children():
            widget.destroy()

        self.status_label.configure(text=f"Scanning {target_path} ... Mohon tunggu (memakan waktu).", text_color="#FFFF00")

        # Jalankan proses scanning di thread terpisah
        threading.Thread(target=self.process_scan, args=(target_path,), daemon=True).start()

    def process_scan(self, target_path):
        folder_data = []
        try:
            # Hanya scan sub-direktori langsung (level 1) dari target path
            with os.scandir(target_path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.is_symlink():
                        # Update status di UI (gunakan self.after agar aman)
                        self.after(0, lambda n=entry.name: self.status_label.configure(text=f"Calculating size for: {n} ..."))
                        
                        # Hitung total ukurannya
                        size = get_dir_size(entry.path)
                        folder_data.append({"name": entry.name, "path": entry.path, "size": size})
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Gagal membaca direktori: {e}"))

        # Urutkan dari size terbesar ke terkecil
        folder_data.sort(key=lambda x: x["size"], reverse=True)

        # Tampilkan ke layar via main thread
        self.after(0, lambda: self.display_results(target_path, folder_data))

    def display_results(self, target_path, folder_data):
        self.status_label.configure(text=f"Scan selesai untuk: {target_path}", text_color="#00FF00")
        
        if not folder_data:
            lbl_empty = ctk.CTkLabel(self.result_scroll, text="Tidak ada sub-folder yang dapat dibaca di lokasi ini.", text_color="gray")
            lbl_empty.pack(pady=20)
        else:
            for item in folder_data:
                row_frame = ctk.CTkFrame(self.result_scroll, fg_color="#333333", corner_radius=5)
                row_frame.pack(fill="x", padx=5, pady=5)

                # Nama Folder
                lbl_name = ctk.CTkLabel(row_frame, text=item["name"], font=ctk.CTkFont(weight="bold"), justify="left", anchor="w")
                lbl_name.pack(side="left", padx=(10, 5), pady=10, fill="x", expand=True)

                # Ukuran Folder
                lbl_size = ctk.CTkLabel(row_frame, text=format_size(item["size"]), width=80, anchor="e")
                lbl_size.pack(side="left", padx=5, pady=10)

                # Tombol Open / Scan
                btn_open = ctk.CTkButton(row_frame, text="Open / Scan", width=90, fg_color="#444444", hover_color="#666666",
                                         command=lambda p=item["path"]: self.scan_subfolder(p))
                btn_open.pack(side="right", padx=(5, 10), pady=10)

                # Tombol Create Link
                btn_link = ctk.CTkButton(row_frame, text="Create Link", width=90, fg_color="#8B0000", hover_color="#A52A2A",
                                         command=lambda p=item["path"]: self.send_to_create_link(p))
                btn_link.pack(side="right", padx=5, pady=10)

        self.btn_scan.configure(state="normal")
        self.btn_browse.configure(state="normal")

    def scan_subfolder(self, path):
        # Update kolom teks path dan otomatis jalankan scan
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, path)
        self.start_scan()

    def send_to_create_link(self, path):
        # Panggil fungsi dari main.py untuk pindah menu
        if self.navigate_to_create_callback:
            self.navigate_to_create_callback(path)