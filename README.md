# Folder Junction Manager (Link Manager)

Sebuah utilitas Windows berbasis GUI yang dirancang untuk memindahkan folder berukuran besar (seperti direktori `AppData`, *cache* aplikasi, atau *save game*) dari drive sistem utama (C:) ke partisi atau drive lain (D:, E:, dll.) **tanpa merusak fungsionalitas aplikasi tersebut**.

Aplikasi ini menggunakan fitur **Directory Junction** (`mklink /j`) bawaan Windows. Sistem operasi dan aplikasi akan tetap mengira bahwa folder tersebut berada di lokasi aslinya, padahal secara fisik data sudah dipindahkan ke drive lain untuk membebaskan ruang penyimpanan.

---

## ✨ Fitur Utama

1. **Size Analyzer:** Pindai dan temukan folder mana yang paling memakan ruang penyimpanan Anda dengan cepat (dilengkapi integrasi langsung ke menu *Create Link*).
2. **Create Link:** Pindahkan folder secara aman. Dilengkapi fitur deteksi file terkunci (*locked files*) dan kemampuan menghentikan proses (*kill process*) secara otomatis agar pemindahan tidak gagal di tengah jalan.
3. **Restore Link (Rollback):** Mengembalikan folder dari drive eksternal ke lokasi sistem aslinya dengan satu klik, menghapus jejak *junction*, dan merapikan kembali ruang kerja Anda.
4. **Link Manager:** Pindahkan folder tujuan ke drive baru (misal dari D: ke E:) secara mulus tanpa harus mengembalikannya ke C: terlebih dahulu. Terdapat juga fitur **Force Delete** untuk menghapus *link* beserta folder sisa (*leftover*) secara permanen.
5. **Database Otomatis:** Menyimpan jejak seluruh *junction* yang pernah dibuat dalam satu file riwayat portabel di `AppData`.

---

## 🛠️ Persyaratan Sistem

- Windows 10 atau Windows 11
- Hak Akses Administrator (Aplikasi akan meminta UAC Prompt saat dijalankan)
- Python 3.8 atau lebih baru (Jika ingin menjalankan dari *source code*)

---

## 🚀 Cara Menjalankan (Source Code)

Jika Anda ingin menjalankan aplikasi ini langsung dari skrip Python:

1. Kloning repositori ini:
   ```bash
   git clone [https://github.com/USERNAME_ANDA/NAMA_REPOSITORI_ANDA.git](https://github.com/USERNAME_ANDA/NAMA_REPOSITORI_ANDA.git)
   cd NAMA_REPOSITORI_ANDA

2. Instal pustaka (libraries) yang dibutuhkan:
   ```bash
   pip install customtkinter psutil

3. Jalankan aplikasi:
   ```bash
   python main.py


------------------------------------------------------

📦 Cara Kompilasi Menjadi File .exe
Jika Anda ingin membuat file .exe yang portabel agar bisa dibagikan dan dijalankan di komputer Windows manapun tanpa perlu menginstal Python:

1. Pastikan Anda sudah menginstal pustaka PyInstaller:
   ```bash
    pip install pyinstaller

2. Buka Terminal/CMD di dalam folder proyek ini, lalu jalankan perintah kompilasi berikut:
   ```bash
    pyinstaller --noconsole --onefile main.py

3. Tunggu hingga proses selesai. File main.exe Anda akan tersedia di dalam folder dist/. Anda bisa mengubah nama file tersebut menjadi FolderJunctionManager.exe dan aplikasi siap digunakan!


--------------------------------------------------------

📖 Tutorial Penggunaan Aplikasi
Tahap 1: Mencari Target (Size Analyzer)
Buka menu Size Analyzer.

Pilih direktori yang ingin Anda periksa (contoh: C:\Users\NamaAnda\AppData).

Klik Scan dan tunggu hingga daftar folder beserta ukurannya muncul.

Temukan folder yang ukurannya sangat besar, lalu klik Create Link di sebelah kanannya. Aplikasi akan otomatis membawa Anda ke menu Create Link.

Tahap 2: Memindahkan Folder (Create Link)
Di menu Create Link, Source Folder akan terisi otomatis jika Anda datang dari Size Analyzer. Jika tidak, Anda bisa mencarinya manual via tombol Browse.

Pada Destination Folder, klik Browse dan pilih lokasi drive baru (misal D:\BackupAplikasi). Nama folder asli akan otomatis ditambahkan ke akhir teks.

Klik Execute & Create Link.

Jika muncul peringatan "File Terkunci", klik Yes agar aplikasi mematikan proses yang menghalangi.

Tunggu proses copy selesai. Junction Link akan dibuat secara otomatis!

Tahap 3: Mengelola Link (Link Manager)
Masuk ke menu Link Manager untuk melihat seluruh daftar junction aktif Anda.

Klik Edit / Move pada salah satu baris.

Anda bisa memindahkan target ke drive lain, atau mengeklik Force Delete jika Anda sudah melakukan uninstall aplikasi terkait dan ingin membersihkan sisa foldernya secara permanen.

Tahap 4: Mengembalikan Folder (Restore Link)
Buka menu Restore Link.

Klik tombol Restore di sebelah baris data yang diinginkan.

Aplikasi akan menghapus link palsu, menyalin kembali file dari drive eksternal ke tempat aslinya, lalu menghapus folder target.

⚠️ Peringatan Keamanan
JANGAN pernah memindahkan folder inti sistem Windows seperti C:\Windows atau C:\Program Files secara keseluruhan, karena dapat menyebabkan Blue Screen (BSOD) atau gagal booting.

Target yang paling aman dan disarankan untuk dipindahkan adalah sub-folder di dalam C:\Users\AppData\Local atau Roaming (misalnya folder cache dari Discord, Spotify, Tencent, Apple, atau aplikasi besar lainnya).

Dikembangkan oleh Satria Aji bersama Gemini.
