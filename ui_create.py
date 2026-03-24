import os
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from database import save_to_db
from utils import find_locking_processes, get_free_space, format_size

class CreateFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.cancel_flag = False
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self, text="Create New Directory Junction", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="w")

        # Source Input
        ctk.CTkLabel(self, text="Source Folder:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_source = ctk.CTkEntry(self, placeholder_text="e.g. C:\\Users\\Name\\AppData\\Roaming\\TargetFolder")
        self.entry_source.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.btn_browse_source = ctk.CTkButton(self, text="Browse", width=80, fg_color="#333333", hover_color="#555555", command=self.browse_source)
        self.btn_browse_source.grid(row=1, column=2, padx=10, pady=10)

        # Destination Input
        ctk.CTkLabel(self, text="Destination Folder:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_dest = ctk.CTkEntry(self, placeholder_text="e.g. D:\\Link\\TargetFolder")
        self.entry_dest.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.btn_browse_dest = ctk.CTkButton(self, text="Browse", width=80, fg_color="#333333", hover_color="#555555", command=self.browse_dest)
        self.btn_browse_dest.grid(row=2, column=2, padx=10, pady=10)

        # Action Buttons (Ditumpuk di posisi yang sama, dikontrol via grid_forget)
        self.btn_execute = ctk.CTkButton(self, text="Execute & Create Link", fg_color="#8B0000", hover_color="#A52A2A", font=ctk.CTkFont(weight="bold"), command=self.start_process)
        self.btn_execute.grid(row=3, column=0, columnspan=3, padx=10, pady=20, sticky="ew")
        
        self.btn_cancel = ctk.CTkButton(self, text="Stop / Cancel", fg_color="#FF8C00", hover_color="#FFA500", font=ctk.CTkFont(weight="bold"), command=self.cancel_action)
        # btn_cancel sengaja tidak di-grid di awal agar tersembunyi

        # Terminal Log
        self.log_box = ctk.CTkTextbox(self, fg_color="#1E1E1E", text_color="#00FF00", font=("Consolas", 12))
        self.log_box.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.log_message("System Ready. Waiting for input...")

    def lock_ui(self):
        # Disable input
        self.entry_source.configure(state="disabled")
        self.entry_dest.configure(state="disabled")
        self.btn_browse_source.configure(state="disabled")
        self.btn_browse_dest.configure(state="disabled")
        
        # Sembunyikan tombol Execute, tampilkan tombol Cancel di posisi yang sama
        self.btn_execute.grid_forget()
        self.btn_cancel.grid(row=3, column=0, columnspan=3, padx=10, pady=20, sticky="ew")
        self.btn_cancel.configure(state="normal", text="Stop / Cancel")

    def unlock_ui(self):
        # Enable input
        self.entry_source.configure(state="normal")
        self.entry_dest.configure(state="normal")
        self.btn_browse_source.configure(state="normal")
        self.btn_browse_dest.configure(state="normal")
        
        # Sembunyikan tombol Cancel, kembalikan tombol Execute
        self.btn_cancel.grid_forget()
        self.btn_execute.grid(row=3, column=0, columnspan=3, padx=10, pady=20, sticky="ew")
        self.btn_execute.configure(state="normal")
        
        self.cancel_flag = False

    def cancel_action(self):
        self.cancel_flag = True
        self.log_message("\n[!] Perintah Stop diterima. Sedang menghentikan proses...")
        self.btn_cancel.configure(state="disabled", text="Stopping...")

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            folder = os.path.normpath(folder)
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            folder = os.path.normpath(folder)
            source_path = self.entry_source.get().strip()
            if source_path:
                folder_name = os.path.basename(os.path.normpath(source_path))
                if folder_name:
                    folder = os.path.join(folder, folder_name)
            self.entry_dest.delete(0, tk.END)
            self.entry_dest.insert(0, folder)

    def log_message(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def start_process(self):
        source = self.entry_source.get().strip()
        dest = self.entry_dest.get().strip()

        if not source or not dest:
            messagebox.showerror("Error", "Source dan Destination tidak boleh kosong!")
            return

        if not os.path.exists(source):
            messagebox.showerror("Error", f"Folder Source tidak ditemukan:\n{source}")
            return

        self.lock_ui()
        self.log_box.delete("1.0", tk.END)
        self.log_message(f"--- MEMULAI PROSES CREATE ---")
        self.log_message(f"Source: {source}")
        self.log_message(f"Destination: {dest}")

        threading.Thread(target=self.process_create_link, args=(source, dest), daemon=True).start()

    def process_create_link(self, source, dest):
        try:
            # 1. Hitung total size dan cek free space
            self.log_message("\n1. Menghitung ukuran folder & mengecek kapasitas drive tujuan...")
            total_size = 0
            for dirpath, _, filenames in os.walk(source):
                for f in filenames:
                    if self.cancel_flag: raise Exception("Dibatalkan oleh user saat menghitung size.")
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)

            free_space = get_free_space(dest)
            self.log_message(f"   Ukuran Source: {format_size(total_size)}")
            self.log_message(f"   Kapasitas Tersedia di Target: {format_size(free_space)}")

            if total_size > free_space:
                raise Exception(f"Kapasitas drive tujuan tidak cukup!\nButuh: {format_size(total_size)}\nTersedia: {format_size(free_space)}")

            # 2. Cek file terkunci
            self.log_message("\n2. Mengecek file yang sedang digunakan...")
            locking_procs = find_locking_processes(source)
            if locking_procs:
                proc_names = ", ".join([p.info['name'] for p in locking_procs])
                self.log_message(f"   [!] Ditemukan proses yang mengunci: {proc_names}")
                
                # Buka UI sementara untuk messagebox
                if messagebox.askyesno("File Terkunci", f"Aplikasi berikut sedang menggunakan folder source:\n{proc_names}\n\nApakah Anda ingin mematikan (kill) aplikasi tersebut secara paksa?"):
                    for p in locking_procs:
                        try:
                            p.kill()
                            self.log_message(f"   [+] Berhasil mematikan: {p.info['name']}")
                        except Exception as e:
                            self.log_message(f"   [-] Gagal mematikan {p.info['name']}: {e}")
                            return
                else:
                    self.log_message("   [x] Proses dibatalkan oleh user.")
                    return
            else:
                self.log_message("   [+] Aman, tidak ada file yang terkunci.")

            # 3. Proses Copy
            self.log_message("\n3. Proses Pemindahan Folder (Copying)...")
            if not os.path.exists(dest):
                os.makedirs(dest)

            copied_size = 0
            def copy_tree_progress(src_dir, dst_dir):
                nonlocal copied_size
                for item in os.listdir(src_dir):
                    if self.cancel_flag:
                        raise Exception("Dibatalkan oleh user saat proses copy.")
                    
                    s = os.path.join(src_dir, item)
                    d = os.path.join(dst_dir, item)
                    if os.path.isdir(s):
                        if not os.path.exists(d):
                            os.makedirs(d)
                        copy_tree_progress(s, d)
                    else:
                        shutil.copy2(s, d)
                        copied_size += os.path.getsize(s)
                        percent = (copied_size / total_size * 100) if total_size > 0 else 100
                        if copied_size % (1024 * 1024) < 500000 or copied_size == total_size:
                            self.log_message(f"   Menyalin: {item} - {percent:.1f}%")

            copy_tree_progress(source, dest)
            self.log_message("   [+] Copy selesai 100%.")

            # 4. Hapus Source Asli
            self.log_message("\n4. Menghapus folder source asli...")
            shutil.rmtree(source)
            self.log_message("   [+] Folder source berhasil dihapus.")

            # 5. Buat Junction
            self.log_message("\n5. Membuat Directory Junction (mklink /j)...")
            command = f'mklink /j "{source}" "{dest}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message(f"   [+] Junction berhasil dibuat:\n   {result.stdout.strip()}")
            else:
                self.log_message(f"   [-] Gagal membuat Junction:\n   {result.stderr.strip()}")
                return

            # 6. Simpan Record
            self.log_message("\n6. Menyimpan record ke database...")
            save_to_db(source, dest)
            self.log_message("   [+] Record berhasil disimpan.")
            self.log_message("\n--- PROSES SELESAI DENGAN SUKSES ---")

            messagebox.showinfo("Sukses", "Folder berhasil dipindahkan dan Link Junction telah dibuat!")

        except Exception as e:
            self.log_message(f"\n[ERROR] {str(e)}")
            messagebox.showerror("Terhenti", f"Proses dihentikan:\n{str(e)}")
        finally:
            self.after(0, self.unlock_ui)