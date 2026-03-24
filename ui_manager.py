import os
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from database import load_db, delete_from_db, save_to_db
from utils import find_locking_processes, get_free_space, format_size

class ManagerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.cancel_flag = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Link Manager (Move Destination)", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=10, pady=(0, 20), sticky="w")

        # Scrollable Frame
        self.manager_scroll = ctk.CTkScrollableFrame(self, fg_color="#2B2B2B")
        self.manager_scroll.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Terminal Log
        self.log_box = ctk.CTkTextbox(self, fg_color="#1E1E1E", text_color="#00FF00", font=("Consolas", 12))
        self.log_box.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Tombol Cancel (Posisi tersembunyi secara default menggunakan trik grid_forget)
        self.btn_cancel = ctk.CTkButton(self, text="Stop / Cancel", fg_color="#FF8C00", hover_color="#FFA500", font=ctk.CTkFont(weight="bold"), command=self.cancel_action)
        # Tidak di-grid di init agar tidak muncul saat idle

        self.log_message("Manager System Ready. Select a link to move its destination...")

    def lock_ui(self):
        # Matikan tombol Edit/Move di list
        for widget in self.manager_scroll.winfo_children():
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
        for widget in self.manager_scroll.winfo_children():
            widget.destroy()

        data = load_db()

        if not data:
            lbl_empty = ctk.CTkLabel(self.manager_scroll, text="Tidak ada record history (Database Kosong).", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        for index, item in enumerate(data):
            row_frame = ctk.CTkFrame(self.manager_scroll, fg_color="#333333", corner_radius=5)
            row_frame.pack(fill="x", padx=5, pady=5)

            info_text = f"Source: {item['source']}\nTarget: {item['destination']}"
            lbl_info = ctk.CTkLabel(row_frame, text=info_text, justify="left", anchor="w")
            lbl_info.pack(side="left", padx=10, pady=10, fill="x", expand=True)

            btn_edit = ctk.CTkButton(row_frame, text="Edit / Move", width=80, fg_color="#8B0000", hover_color="#A52A2A", 
                                        command=lambda r=item: self.open_edit_popup(r))
            btn_edit.pack(side="right", padx=10, pady=10)

    def open_edit_popup(self, record):
        popup = ctk.CTkToplevel(self)
        popup.title("Edit Destination")
        popup.geometry("600x250")
        popup.transient(self.winfo_toplevel())
        popup.grab_set() 

        ctk.CTkLabel(popup, text="Move Destination Folder", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(popup, text="Current Target:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(popup, text=record['destination'], text_color="gray").grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(popup, text="New Target:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        entry_new_dest = ctk.CTkEntry(popup, width=300)
        entry_new_dest.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        def browse_new_dest():
            folder = filedialog.askdirectory()
            if folder:
                folder = os.path.normpath(folder)
                folder_name = os.path.basename(os.path.normpath(record['source']))
                if folder_name:
                    folder = os.path.join(folder, folder_name)
                entry_new_dest.delete(0, tk.END)
                entry_new_dest.insert(0, folder)

        btn_browse = ctk.CTkButton(popup, text="Browse", width=80, fg_color="#333333", hover_color="#555555", command=browse_new_dest)
        btn_browse.grid(row=2, column=2, padx=10, pady=10)

        def execute():
            new_dest = entry_new_dest.get().strip()
            if not new_dest:
                messagebox.showerror("Error", "Folder target baru tidak boleh kosong!", parent=popup)
                return
            if new_dest.lower() == record['destination'].lower():
                messagebox.showerror("Error", "Folder target baru sama dengan yang lama!", parent=popup)
                return
            
            popup.destroy()
            self.lock_ui()
            self.log_box.delete("1.0", tk.END)
            self.log_message(f"--- MEMULAI PROSES PEMINDAHAN TARGET (MANAGER) ---")
            self.log_message(f"Junction Source: {record['source']}")
            self.log_message(f"Target Lama: {record['destination']}")
            self.log_message(f"Target Baru: {new_dest}")

            threading.Thread(target=self.process_move, args=(record['source'], record['destination'], new_dest), daemon=True).start()

        # Layout Tombol pada Popup
        btn_execute = ctk.CTkButton(popup, text="Execute Move", fg_color="#8B0000", hover_color="#A52A2A", command=execute)
        btn_execute.grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        btn_force_delete = ctk.CTkButton(popup, text="Force Delete", fg_color="#CC0000", hover_color="#EE0000", command=lambda: self.start_force_delete(record, popup))
        btn_force_delete.grid(row=3, column=2, padx=10, pady=20, sticky="ew")

    # --- LOGIKA MOVE (PINDAH DESTINATION) ---
    def process_move(self, source, old_dest, new_dest):
        try:
            # 1. Cek Space Target Baru
            self.log_message("\n1. Menghitung ukuran folder & mengecek kapasitas drive target baru...")
            total_size = 0
            if os.path.exists(old_dest):
                for dirpath, _, filenames in os.walk(old_dest):
                    for f in filenames:
                        if self.cancel_flag: raise Exception("Dibatalkan saat menghitung size.")
                        fp = os.path.join(dirpath, f)
                        if not os.path.islink(fp):
                            total_size += os.path.getsize(fp)

            free_space = get_free_space(new_dest)
            self.log_message(f"   Ukuran Target Lama: {format_size(total_size)}")
            self.log_message(f"   Kapasitas Tersedia di Drive Baru: {format_size(free_space)}")

            if total_size > free_space:
                 raise Exception(f"Kapasitas drive baru tidak cukup!\nButuh: {format_size(total_size)}\nTersedia: {format_size(free_space)}")

            # 2. Cek Proses Terkunci
            self.log_message("\n2. Mengecek file yang sedang digunakan di lokasi target lama...")
            locking_procs = find_locking_processes(old_dest)
            if locking_procs:
                proc_names = ", ".join([p.info['name'] for p in locking_procs])
                self.log_message(f"   [!] Ditemukan proses yang mengunci: {proc_names}")
                
                if messagebox.askyesno("File Terkunci", f"Aplikasi berikut sedang menggunakan folder yang akan dipindah:\n{proc_names}\n\nApakah Anda ingin mematikan (kill) aplikasi tersebut?"):
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

            # 3. Copy ke lokasi baru TERLEBIH DAHULU
            self.log_message("\n3. Proses Memindahkan Folder ke Lokasi Baru (Copying)...")
            if not os.path.exists(new_dest):
                os.makedirs(new_dest)

            if os.path.exists(old_dest):
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
                                self.log_message(f"   Memindahkan: {item} - {percent:.1f}%")

                copy_tree_progress(old_dest, new_dest)
                self.log_message("   [+] Copy ke lokasi baru selesai 100%.")
            else:
                self.log_message("   [-] Folder target lama tidak ditemukan. Melewati proses copy.")

            # 4. Hapus Junction Link Lama (Setelah copy sukses)
            self.log_message("\n4. Menghapus Junction lama...")
            if os.path.exists(source):
                command = f'rmdir "{source}"'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_message("   [+] Junction berhasil dihapus.")
                else:
                    self.log_message(f"   [-] Gagal menghapus Junction:\n   {result.stderr.strip()}")
            else:
                self.log_message("   [!] Junction tidak ditemukan. Melanjutkan...")

            # 5. Buat Junction Baru
            self.log_message("\n5. Membuat Directory Junction Baru (mklink /j)...")
            command = f'mklink /j "{source}" "{new_dest}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message(f"   [+] Junction baru berhasil dibuat:\n   {result.stdout.strip()}")
            else:
                self.log_message(f"   [-] Gagal membuat Junction:\n   {result.stderr.strip()}")
                return

            # 6. Hapus Old Dest
            self.log_message("\n6. Menghapus folder target yang lama...")
            if os.path.exists(old_dest):
                shutil.rmtree(old_dest)
                self.log_message("   [+] Folder target lama berhasil dihapus.")

            # 7. Update Database
            self.log_message("\n7. Memperbarui record database...")
            delete_from_db(source, old_dest)
            save_to_db(source, new_dest)
            self.log_message("   [+] Record berhasil diperbarui.")
            
            self.log_message("\n--- PROSES PEMINDAHAN SELESAI DENGAN SUKSES ---")
            messagebox.showinfo("Sukses", "Target folder berhasil dipindahkan dan Junction telah diperbarui!")

        except Exception as e:
            self.log_message(f"\n[ERROR] {str(e)}")
            messagebox.showerror("Terhenti", f"Proses dihentikan:\n{str(e)}\n\n(Catatan: Link lama belum dicabut, aman)")
        finally:
            self.after(0, self.unlock_ui)

    # --- LOGIKA FORCE DELETE ---
    def start_force_delete(self, record, popup):
        # Konfirmasi keamanan sebelum menghapus
        if not messagebox.askyesno("PERINGATAN BAHAYA", f"Anda akan MENGHAPUS SECARA PERMANEN:\n\n1. Link: {record['source']}\n2. Folder & Isi: {record['destination']}\n\nTindakan ini tidak bisa dibatalkan.\nApakah Anda yakin ingin melanjutkan?", parent=popup):
            return
        
        popup.destroy()
        self.lock_ui()
        self.log_box.delete("1.0", tk.END)
        self.log_message(f"--- MEMULAI PROSES FORCE DELETE ---")
        self.log_message(f"Link Source: {record['source']}")
        self.log_message(f"Folder Destination: {record['destination']}")

        threading.Thread(target=self.process_force_delete, args=(record['source'], record['destination']), daemon=True).start()

    def process_force_delete(self, source, dest):
        try:
            # 1. Cek Proses Terkunci
            self.log_message("\n1. Mengecek file yang sedang digunakan di lokasi target...")
            locking_procs = find_locking_processes(dest)
            if locking_procs:
                proc_names = ", ".join([p.info['name'] for p in locking_procs])
                self.log_message(f"   [!] Ditemukan proses yang mengunci: {proc_names}")
                
                if messagebox.askyesno("File Terkunci", f"Aplikasi berikut sedang menggunakan folder yang akan dihapus:\n{proc_names}\n\nApakah Anda ingin mematikan (kill) aplikasi tersebut secara paksa?"):
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

            # 2. Hapus Junction Link
            self.log_message("\n2. Menghapus Junction (Link)...")
            if os.path.exists(source):
                command = f'rmdir "{source}"'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_message("   [+] Junction berhasil dihapus.")
                else:
                    self.log_message(f"   [-] Gagal menghapus Junction:\n   {result.stderr.strip()}")
            else:
                self.log_message("   [!] Junction tidak ditemukan (Mungkin sudah terhapus manual).")

            # 3. Hapus Destination Folder
            self.log_message("\n3. Menghapus Folder Destination beserta isinya...")
            if os.path.exists(dest):
                shutil.rmtree(dest)
                self.log_message("   [+] Folder Destination berhasil dihapus permanen.")
            else:
                self.log_message("   [!] Folder Destination tidak ditemukan.")

            # 4. Update Database
            self.log_message("\n4. Menghapus record dari database...")
            delete_from_db(source, dest)
            self.log_message("   [+] Record berhasil dihapus.")
            
            self.log_message("\n--- PROSES FORCE DELETE SELESAI DENGAN SUKSES ---")
            messagebox.showinfo("Sukses", "Force Delete berhasil. Link dan folder telah dihapus permanen!")

        except Exception as e:
            self.log_message(f"\n[ERROR] {str(e)}")
            messagebox.showerror("Terhenti", f"Proses dihentikan:\n{str(e)}")
        finally:
            self.after(0, self.unlock_ui)