import os
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from database import load_db, delete_from_db
from utils import find_locking_processes, get_free_space, format_size

class RestoreFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.cancel_flag = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Restore Directory Junction", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=10, pady=(0, 20), sticky="w")

        self.restore_scroll = ctk.CTkScrollableFrame(self, fg_color="#2B2B2B")
        self.restore_scroll.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.log_box = ctk.CTkTextbox(self, fg_color="#1E1E1E", text_color="#00FF00", font=("Consolas", 12))
        self.log_box.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Tombol Cancel (Posisi tersembunyi secara default menggunakan trik grid_forget)
        self.btn_cancel = ctk.CTkButton(self, text="Stop / Cancel", fg_color="#FF8C00", hover_color="#FFA500", font=ctk.CTkFont(weight="bold"), command=self.cancel_action)
        # Tidak di-grid di init agar tidak muncul saat idle

        self.log_message("Restore System Ready. Select a link to restore...")

    def lock_ui(self):
        # Matikan semua tombol "Restore" di dalam list
        for widget in self.restore_scroll.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state="disabled")
        
        # Munculkan tombol Stop/Cancel
        self.btn_cancel.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.btn_cancel.configure(state="normal", text="Stop / Cancel")

    def unlock_ui(self):
        self.refresh_list()
        
        # Sembunyikan kembali tombol Stop/Cancel
        self.btn_cancel.grid_forget()
        self.cancel_flag = False

    def cancel_action(self):
        self.cancel_flag = True
        self.log_message("\n[!] Perintah Stop diterima. Sedang menghentikan proses...")
        self.btn_cancel.configure(state="disabled", text="Stopping...")

    def log_message(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def refresh_list(self):
        for widget in self.restore_scroll.winfo_children():
            widget.destroy()

        data = load_db()

        if not data:
            lbl_empty = ctk.CTkLabel(self.restore_scroll, text="Tidak ada record history (Database Kosong).", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        for index, item in enumerate(data):
            row_frame = ctk.CTkFrame(self.restore_scroll, fg_color="#333333", corner_radius=5)
            row_frame.pack(fill="x", padx=5, pady=5)

            info_text = f"Source: {item['source']}\nTarget: {item['destination']}"
            lbl_info = ctk.CTkLabel(row_frame, text=info_text, justify="left", anchor="w")
            lbl_info.pack(side="left", padx=10, pady=10, fill="x", expand=True)

            btn_restore = ctk.CTkButton(row_frame, text="Restore", width=80, fg_color="#8B0000", hover_color="#A52A2A", 
                                        command=lambda r=item: self.start_restore(r))
            btn_restore.pack(side="right", padx=10, pady=10)

    def start_restore(self, record):
        if not messagebox.askyesno("Konfirmasi Restore", f"Anda yakin ingin mengembalikan folder ini?\n\nDari: {record['destination']}\nKe: {record['source']}"):
            return

        self.lock_ui()
        self.log_box.delete("1.0", tk.END)
        self.log_message(f"--- MEMULAI PROSES RESTORE (ROLLBACK) ---")
        self.log_message(f"Target saat ini: {record['destination']}")
        self.log_message(f"Dikembalikan ke: {record['source']}")

        threading.Thread(target=self.process_restore, args=(record['source'], record['destination']), daemon=True).start()

    def process_restore(self, source, dest):
        try:
            # 1. Pengecekan Size (Kapasitas drive lama/Source)
            self.log_message("\n1. Menghitung ukuran folder & mengecek kapasitas drive asal...")
            total_size = 0
            if os.path.exists(dest):
                for dirpath, _, filenames in os.walk(dest):
                    for f in filenames:
                        if self.cancel_flag: raise Exception("Dibatalkan saat menghitung size.")
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)

            free_space = get_free_space(source)
            self.log_message(f"   Ukuran Target: {format_size(total_size)}")
            self.log_message(f"   Kapasitas Tersedia di Drive Asal: {format_size(free_space)}")

            if total_size > free_space:
                 raise Exception(f"Kapasitas drive asal tidak cukup untuk rollback!\nButuh: {format_size(total_size)}\nTersedia: {format_size(free_space)}")

            # 2. Cek File Terkunci
            self.log_message("\n2. Mengecek file yang sedang digunakan di lokasi target...")
            locking_procs = find_locking_processes(dest)
            if locking_procs:
                proc_names = ", ".join([p.info['name'] for p in locking_procs])
                self.log_message(f"   [!] Ditemukan proses yang mengunci: {proc_names}")
                
                if messagebox.askyesno("File Terkunci", f"Aplikasi berikut sedang menggunakan folder yang akan di-restore:\n{proc_names}\n\nApakah Anda ingin mematikan (kill) aplikasi tersebut?"):
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

            # 3. Hapus Junction
            self.log_message("\n3. Menghapus Junction lama...")
            if os.path.exists(source):
                command = f'rmdir "{source}"'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_message("   [+] Junction berhasil dihapus.")
                else:
                    self.log_message(f"   [-] Gagal menghapus Junction:\n   {result.stderr.strip()}")
            else:
                self.log_message("   [!] Junction tidak ditemukan. Melanjutkan...")

            # 4. Copy kembali
            self.log_message("\n4. Proses Mengembalikan Folder (Copying)...")
            if not os.path.exists(source):
                os.makedirs(source)

            if os.path.exists(dest):
                copied_size = 0
                def copy_tree_progress(src_dir, dst_dir):
                    nonlocal copied_size
                    for item in os.listdir(src_dir):
                        if self.cancel_flag: raise Exception("Dibatalkan oleh user saat proses copy.")
                        
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
                                self.log_message(f"   Mengembalikan: {item} - {percent:.1f}%")

                copy_tree_progress(dest, source)
                self.log_message("   [+] Copy pengembalian selesai 100%.")

                # 5. Hapus Dest Asli
                self.log_message("\n5. Menghapus folder target yang lama...")
                shutil.rmtree(dest)
                self.log_message("   [+] Folder target berhasil dihapus.")
            else:
                self.log_message("   [-] Folder target asal tidak ditemukan. Melewati proses copy.")

            # 6. Hapus Record
            self.log_message("\n6. Menghapus record dari history database...")
            delete_from_db(source, dest)
            self.log_message("   [+] Record berhasil dihapus.")
            
            self.log_message("\n--- PROSES RESTORE SELESAI DENGAN SUKSES ---")
            messagebox.showinfo("Sukses", "Folder berhasil dikembalikan seperti semula!")

        except Exception as e:
            self.log_message(f"\n[ERROR] {str(e)}")
            messagebox.showerror("Terhenti", f"Proses dihentikan:\n{str(e)}")
        finally:
            self.after(0, self.unlock_ui)