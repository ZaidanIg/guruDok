# GuruDok — Platform Otomasi Administrasi Guru

Platform Otomasi Dokumen Administrasi Guru SD/SMP/SMA berbasis **Template Deterministik 100% Resmi** sesuai regulasi **Kepka BSKAP No. 046/H/KR/2025**, **Permendikdasmen No. 13/2025** (Alokasi JP), dan **Permendikdasmen No. 10/2025** (8 Dimensi Profil Lulusan).

---

## 📁 Struktur Direktori Proyek

* **`backend/`** — REST API FastAPI, Document Engine (Word `.docx`, Excel `.xlsx`, PDF `.pdf`), Security Guard, dan koneksi database PostgreSQL (`GuruDocDB`).
* **`frontend/`** — Aplikasi web SPA berbasis Vite + React 18 + TypeScript + Tailwind CSS dengan gaya desain **Claymorphism (Soft 3D Tactile)**.
* **`document/`** — Dokumen spesifikasi teknis (BRD, SRS, UI/UX Spec, API Routes, Schema SQL, dan panduan deployment).
* **`rule/`** — Konstitusi dan aturan kerja proyek (Sprint Workflow, Zero-Trust Verification, Standar Kurikulum, Backend OOP, Claymorphism, TDD).
* **`plan/`** — Arsip dokumen Sprint Plan formal per sprint.
* **`todo/`** — Daftar pekerjaan aktif (Active Sprint ToDo) dan log riwayat perubahan (*changelog*).

---

## 🛠️ Prasyarat Sistem (Prerequisites)

Sebelum menjalankan aplikasi secara lokal, pastikan perangkat Anda telah terpasang:
1. **Python:** Versi 3.10 atau yang lebih baru (mendukung Python 3.11, 3.12, 3.13, 3.14).
2. **Node.js:** Versi 18 LTS atau 20 LTS (termasuk package manager `npm`).
3. **Git:** Untuk manajemen version control.
4. **PostgreSQL (Opsional untuk dev lokal):** Jika ingin menghubungkan ke database lokal `GuruDocDB`.

---

## 🚀 Panduan Menjalankan Aplikasi Secara Manual

Anda dapat menjalankan backend dan frontend secara manual di dua terminal terpisah:

### 1. Menjalankan Backend (FastAPI)

#### A. Persiapan Lingkungan Virtual & Dependencies (Hanya saat pertama kali)
Buka terminal di root proyek `e:\project\bisnis-ide`:

```powershell
# 1. Buat virtual environment jika belum ada
python -m venv backend\.venv

# 2. Install dependencies backend
.\backend\.venv\Scripts\python.exe -m pip install --upgrade pip
.\backend\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 3. Siapkan file environment
copy backend\.env.example backend\.env   # (atau buat backend\.env sesuai kebutuhan)
```

#### B. Menjalankan Server Backend
Pilih salah satu cara di bawah ini:

* **Cara 1: Menggunakan Script Cepat (Direkomendasikan)**
  ```cmd
  run-backend
  ```
  *atau di PowerShell:*
  ```powershell
  .\run-backend
  ```
  *(Script ini otomatis mengisolasi `PYTHONPATH` sehingga reload server berjalan mulus tanpa error module).*

* **Cara 2: Menggunakan Python Langsung**
  ```powershell
  .\backend\.venv\Scripts\python.exe run-backend.py
  ```

* **Cara 3: Menggunakan Uvicorn Murni Manual**
  * Di **PowerShell**:
    ```powershell
    $env:PYTHONPATH='backend'
    .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ```
  * Di **Command Prompt (CMD)**:
    ```cmd
    cd backend
    ..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ```

Setelah berhasil dijalankan, server backend aktif di:
* **Base URL:** `http://127.0.0.1:8000`
* **Dokumentasi OpenAPI (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Dokumentasi ReDoc:** `http://127.0.0.1:8000/redoc`

---

### 2. Menjalankan Frontend (Vite + React)

Buka terminal kedua (terpisah dari terminal backend):

```powershell
# 1. Pindah ke direktori frontend
cd frontend

# 2. Install dependencies node modules (hanya saat pertama kali)
npm install

# 3. Jalankan development server Vite
npm run dev
```

Setelah berhasil dijalankan, antarmuka web aktif di:
* **Web UI URL:** `http://localhost:5173`

---

## ⚡ Opsi Cepat: Menjalankan Sekaligus (One-Click Launcher)

Untuk kemudahan pengembangan sehari-hari, Anda dapat menjalankan Backend dan Frontend sekaligus dalam jendela terminal terpisah dengan satu perintah dari root proyek:

* **Windows Command Prompt:**
  ```cmd
  start-dev.bat
  ```
* **Windows PowerShell:**
  ```powershell
  .\start-dev.ps1
  ```

---

## 🧪 Menjalankan Pengujian (Zero-Trust Testing)

Seluruh perubahan kode wajib lolos verifikasi sebelum digabung atau dirilis:

```powershell
# 1. Menjalankan Automated Unit & Integration Tests Backend (pytest - 106 tests)
powershell -Command "$env:PYTHONPATH='backend'; .\backend\.venv\Scripts\pytest.exe backend/tests"

# 2. Menjalankan Type-Checking TypeScript & Build Bundling Frontend
npm --prefix frontend run build
```

---

## 🌿 Aturan Branching & Workflow

Sesuai aturan kerja proyek di [`AGENTS.md`](./AGENTS.md) dan [`rule/`](./rule/):
* **Branch `staging` (`gurudok-staging.duckdns.org`):** Seluruh aktivitas koding, implementasi fitur sprint, dan uji coba wajib dilakukan di branch ini.
* **Branch `main` (`gurudok.guru`):** Branch produksi murni. Dilarang keras melakukan koding langsung di branch ini. Branch `main` hanya menerima merge dari `staging` setelah seluruh pengujian Zero-Trust berstatus **100% PASS**.
