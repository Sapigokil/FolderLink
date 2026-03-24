import sys
import tkinter as tk # Diperlukan untuk tk.END
import customtkinter as ctk

from utils import is_admin
from ui_create import CreateFrame
from ui_restore import RestoreFrame
from ui_manager import ManagerFrame
from ui_sizetree import SizeTreeFrame

# --- PENGECEKAN ADMINISTRATOR ---
if not is_admin():
    import ctypes
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# --- KONFIGURASI TEMA ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Folder Junction Manager")
        self.geometry("950x650") 
        self.minsize(850, 550)

        # Konfigurasi Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- SIDEBAR ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Link Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_menu_create = ctk.CTkButton(self.sidebar_frame, text="Create Link", fg_color="#8B0000", hover_color="#A52A2A", border_width=1, command=self.show_create_frame)
        self.btn_menu_create.grid(row=1, column=0, padx=20, pady=10)

        self.btn_menu_restore = ctk.CTkButton(self.sidebar_frame, text="Restore Link", fg_color="transparent", hover_color="#A52A2A", border_width=1, command=self.show_restore_frame)
        self.btn_menu_restore.grid(row=2, column=0, padx=20, pady=10)

        self.btn_menu_manager = ctk.CTkButton(self.sidebar_frame, text="Link Manager", fg_color="transparent", hover_color="#A52A2A", border_width=1, command=self.show_manager_frame)
        self.btn_menu_manager.grid(row=3, column=0, padx=20, pady=10)

        self.btn_menu_sizetree = ctk.CTkButton(self.sidebar_frame, text="Size Analyzer", fg_color="transparent", hover_color="#A52A2A", border_width=1, command=self.show_sizetree_frame)
        self.btn_menu_sizetree.grid(row=4, column=0, padx=20, pady=10)

        # --- FOOTER COPYRIGHT ---
        # REVISI: Ukuran font diperbesar menjadi 14
        self.footer_label = ctk.CTkLabel(self.sidebar_frame, text="©Satria_Aji with Gemini", font=ctk.CTkFont(size=14))
        self.footer_label.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # --- INISIALISASI FRAMES ---
        self.create_frame = CreateFrame(self, corner_radius=0, fg_color="transparent")
        self.restore_frame = RestoreFrame(self, corner_radius=0, fg_color="transparent")
        self.manager_frame = ManagerFrame(self, corner_radius=0, fg_color="transparent")
        
        self.sizetree_frame = SizeTreeFrame(self, navigate_to_create_callback=self.go_to_create_link_with_path, corner_radius=0, fg_color="transparent")

        # Tampilkan menu pertama saat aplikasi dibuka
        self.show_create_frame()

    # --- LOGIKA NAVIGASI MENU ---
    def hide_all_frames(self):
        self.create_frame.grid_forget()
        self.restore_frame.grid_forget()
        self.manager_frame.grid_forget()
        self.sizetree_frame.grid_forget()

        self.btn_menu_create.configure(fg_color="transparent")
        self.btn_menu_restore.configure(fg_color="transparent")
        self.btn_menu_manager.configure(fg_color="transparent")
        self.btn_menu_sizetree.configure(fg_color="transparent")

    def show_create_frame(self):
        self.hide_all_frames()
        self.create_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_menu_create.configure(fg_color="#8B0000")

    def show_restore_frame(self):
        self.hide_all_frames()
        self.restore_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_menu_restore.configure(fg_color="#8B0000")
        self.restore_frame.refresh_list()

    def show_manager_frame(self):
        self.hide_all_frames()
        self.manager_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_menu_manager.configure(fg_color="#8B0000")
        self.manager_frame.refresh_list()

    def show_sizetree_frame(self):
        self.hide_all_frames()
        self.sizetree_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.btn_menu_sizetree.configure(fg_color="#8B0000")

    # --- LOGIKA KOMUNIKASI LINTAS MENU ---
    def go_to_create_link_with_path(self, source_path):
        self.show_create_frame()
        self.create_frame.entry_source.delete(0, tk.END)
        self.create_frame.entry_source.insert(0, source_path)

if __name__ == "__main__":
    app = App()
    app.mainloop()