# Sprint 41 — Pemisahan Tegas Bagian A (Pilihan Ganda) & Bagian B (Essai) pada Form, Bank Soal, Preview, dan Engine Dokumen

> **Status Dokumen:** `VERIFIED_DONE`  
> **Tanggal:** 24 November 2026  
> **Branch Target:** `staging` (`gurudok-staging.duckdns.org`)  
> **Branch Terlarang:** `main` (Branch produksi murni — dilarang menyentuh kode di `main`)  
> **Rujukan Regulasi & Standar:** Kepka BSKAP No. 046/H/KR/2025, Permendikdasmen No. 13/2025, Permendikdasmen No. 10/2025, PPA Revisi 2025  

---

## 1. Latar Belakang & Kesepakatan `/grill-me`

Pada format evaluasi standar kurikulum sekolah Indonesia (Kuis Harian/S10, Sumatif Bab/S11, dan STS/SAS/S12), naskah evaluasi selalu dipisahkan secara tegas dan berurutan menjadi dua bagian independen:
1. **Bagian A: Soal Pilihan Ganda**
2. **Bagian B: Soal Essai / Uraian**

Berdasarkan wawancara interaktif `/grill-me`, telah disepakati 4 keputusan desain utama:

1. **Sistem Penomoran Soal (Naskah & Kisi-Kisi):**
   * **Nomor Direset per Bagian:**
     * Bagian A (Pilihan Ganda): Nomor 1, 2, 3, ... $N$.
     * Bagian B (Essai): Nomor 1, 2, 3, ... $M$.
     * Pada Kisi-Kisi: Nomor soal tertera 1, 2, ... $N$ untuk Pilihan Ganda dan 1, 2, ... $M$ untuk Essai/Uraian.
     * Pada Kunci Jawaban & Rubrik: Diberi identitas `A.1, A.2, ...` dan `B.1, B.2, ...` agar memudahkan guru saat mencocokkan lembar jawaban.

2. **Tata Letak Form Pembuat Soal (`QuestionBuilderSection.tsx`):**
   * **Dua Seksi Kartu Berurutan (Stacked Sections):**
     * **Seksi Atas — Bagian A: Soal Pilihan Ganda (PG):**
       * Header seksi dengan badge visual Claymorphism bertuliskan `Bagian A: Soal Pilihan Ganda` serta counter jumlah soal PG.
       * Daftar kartu soal PG berurutan (`PG #1`, `PG #2`, dst.) lengkap dengan opsi A–D/E, 1-klik kunci jawaban, level kognitif (Mudah/Sedang/HOTS), pemilih TP, dan stimulus.
       * Tombol aksi `+ Tambah Soal PG` di kaki seksi A.
     * **Seksi Bawah — Bagian B: Soal Essai:**
       * Header seksi dengan badge visual Claymorphism bertuliskan `Bagian B: Soal Essai` serta counter jumlah soal Essai.
       * Daftar kartu soal Essai berurutan (`Essai #1`, `Essai #2`, dst.) lengkap dengan textarea pertanyaan, rubrik/kunci jawaban uraian, level kognitif, pemilih TP, dan stimulus.
       * Tombol aksi `+ Tambah Soal Essai` di kaki seksi B.

3. **Alur Tombol "Ambil dari Bank Soal":**
   * **Tombol Tunggal Global Cerdas di Header Editor:**
     * Tetap 1 tombol ringkas dan efisien di bilah atas: *"Ambil dari Bank Soal"*.
     * Saat diklik, sistem mengambil data dari API `GET /api/v1/questions` (lintas tipe soal) dan mendistribusikan secara otomatis:
       * Soal bertipe `PG` langsung mengisi ke Bagian A.
       * Soal bertipe `URAIAN` langsung mengisi ke Bagian B.
     * Menampilkan notifikasi informatif: *"Berhasil memuat X butir dari Bank Soal (Y PG di Bagian A, Z Essai di Bagian B)!"*.

4. **Format Stimulus Tanpa Box/Shape & Tanpa Kata "Stimulus":**
   * Sesuai mandat: Teks stimulus wajib dirender sebagai teks paragraf bacaan murni di atas pertanyaan, **tanpa shape/border/background kotak** dan **tanpa label/kata 'Stimulus'**.
   * Berlaku seragam di Live Preview (`DocumentGenerator.tsx`), Naskah Word (`.docx`), dan Naskah PDF (`.pdf`).

---

## 2. Zero-Trust Baseline Audit

| Area / File | Kondisi Aktual | Gap / Rencana Pembaruan Sprint 41 |
|---|---|---|
| `frontend/src/components/curriculum/QuestionBuilderSection.tsx` | Kartu soal masih bercampur dalam list linear tunggal `items.map()`. Tombol tambah di footer mencampur PG dan Uraian di bawah. | Refactor ke struktur 2 kontainer stacked: `Bagian A (PG)` dan `Bagian B (Essai)`. Masing-masing kontainer punya header, daftar kartu terfilter, penomoran independen 1..N & 1..M, serta tombol `+ Tambah Soal` masing-masing. |
| `frontend/src/components/sections/DocumentGenerator.tsx` | Live Document Preview masih merender naskah soal dalam 1 list linear 1..Total. | Pisahkan tampilan preview Naskah Soal menjadi `A. Soal Pilihan Ganda` (1..N) dan `B. Soal Essai` (1..M). Sesuaikan penomoran Kisi-Kisi dan tabel Kunci Jawaban. |
| `backend/app/services/document_engine/question_blueprint.py` | Blueprint engine sudah membagi `pg_questions` dan `essai_questions`, namun penomoran `section_no` perlu dipastikan konsisten 1..N dan 1..M saat paket B diacak. | Verifikasi dan pastikan `section_no` bernilai 1..N untuk PG dan 1..M untuk Essai, serta field `bagian` ('A'/'B') terpasang di setiap soal. |
| `backend/app/services/document_engine/docx_engine.py` | Naskah soal di DOCX sudah mengelompokkan `A. Soal Pilihan Ganda` dan `B. Soal Essai` menggunakan `section_no`. | Verifikasi sinkronisasi tabel Kisi-kisi dan Kunci Jawaban agar selaras dengan reset nomor per bagian. |
| `backend/app/services/document_engine/pdf_engine.py` | Engine PDF sudah memecah rendering `A. Soal Pilihan Ganda` dan `B. Soal Essai`. | Verifikasi layout margin, tabel kisi-kisi, dan tabel kunci jawaban. |
| `backend/tests/test_question_blueprint_sprint40.py` | 13 test blueprint eksisting memeriksa struktur dasar blueprint dan persentase skor. | Tambahkan test suite baru untuk memverifikasi penomoran reset per bagian (Bagian A: 1..N, Bagian B: 1..M) pada blueprint, DOCX, dan PDF. |

---

## 3. Rencana Eksekusi Teknis (Task Breakdown)

### Task 1: Refactoring UI Form `QuestionBuilderSection.tsx`
* Pisahkan state `items` menjadi 2 kelompok visual yang tersinkronisasi:
  1. Kontainer **Bagian A: Soal Pilihan Ganda**:
     * Header seksi `.clay-subcard` dengan badge warna biru/teal: `Bagian A: Soal Pilihan Ganda` + counter `(X Soal)`.
     * Render kartu-kartu PG dengan nomor `PG #1`, `PG #2`, ... `PG #X`.
     * Tombol `+ Tambah Soal PG` di bawah daftar kartu PG.
  2. Kontainer **Bagian B: Soal Essai**:
     * Header seksi `.clay-subcard` dengan badge warna amber/emerald: `Bagian B: Soal Essai` + counter `(Y Soal)`.
     * Render kartu-kartu Essai dengan nomor `Essai #1`, `Essai #2`, ... `Essai #Y`.
     * Tombol `+ Tambah Soal Essai` di bawah daftar kartu Essai.
* Tombol aksi tiap kartu:
  * Tombol pindah urutan (naik/turun) beroperasi di dalam lingkup bagian masing-masing.
  * Tombol duplikat dan hapus beroperasi dengan aman memperbarui state global `items`.
  * Tombol alih tipe (misal tombol "Jadikan Essai" atau "Jadikan PG") memungkinkan guru memindahkan soal dari Bagian A ke Bagian B atau sebaliknya secara instan.

### Task 2: Peningkatan Cerdas Tombol "Ambil dari Bank Soal"
* Satu tombol global di header form: *"Ambil dari Bank Soal"*.
* Mengambil daftar soal dari API `GET /api/v1/questions?subject_id=...&jenjang=...`.
* Mengurutkan dan memisahkan soal secara deterministik:
  * Soal PG dialokasikan ke Bagian A.
  * Soal Uraian dialokasikan ke Bagian B.
* Jika bank soal hanya memiliki soal PG atau hanya Uraian, sistem tetap mengisi bagian yang sesuai dan memberikan feedback ringkas.

### Task 3: Sinkronisasi Live Document Preview `DocumentGenerator.tsx`
* Naskah Soal Evaluasi:
  * Menampilkan sub-heading `A. Soal Pilihan Ganda`:
    * Butir nomor 1..N bertipe PG beserta opsi A, B, C, D (atau E).
    * Paragraf teks stimulus polos di atas pertanyaan jika tersedia (tanpa box/shape dan tanpa kata "Stimulus").
  * Menampilkan sub-heading `B. Soal Essai`:
    * Butir nomor 1..M bertipe Essai beserta garis tempat jawaban siswa.
    * Paragraf teks stimulus polos jika tersedia.
* Kisi-Kisi Soal:
  * Nomor soal menampilkan format nomor per bagian (1..N untuk PG, 1..M untuk Essai) atau label kelompok yang jelas.
* Kunci Jawaban & Pedoman Penskoran:
  * Kolom No menampilkan `A.1, A.2, ...` untuk PG dan `B.1, B.2, ...` untuk Essai.

### Task 4: Verifikasi & Pengujian Backend Document Engine
* Memastikan `question_blueprint.py` mengembalikan struktur:
  * `bp["pg_questions"]` dengan nomor 1..N.
  * `bp["essai_questions"]` dengan nomor 1..M.
  * `bp["questions"]` gabungan terurut (seluruh PG lalu seluruh Essai) untuk tabel kisi-kisi dan kunci jawaban.
* Memastikan DOCX dan PDF engine merender Bagian A dan Bagian B tanpa regresi styling.

### Task 5: Zero-Trust Verification & Automated Tests
1. **Pytest Suite:** Tambahkan test case di `backend/tests/` untuk memverifikasi pemisahan dua bagian dan reset nomor soal. Target: Seluruh test (121+ test) **100% PASS**.
2. **Frontend TypeScript Build:** Eksekusi `npm run build` di direktori `frontend/`. Target: **0 errors, 0 warnings**.

---

## 4. Komitmen Keamanan & Kontrak Kerja

1. **Git Isolation:** Seluruh pekerjaan dilakukan di branch **`staging`**, branch `main` tidak disentuh.
2. **Claymorphism Standard:** Menggunakan 100% CSS styling yang sudah ada (`.clay-card`, `.clay-subcard`, `.clay-btn-primary`, `.clay-btn-white`, `.clay-badge`), tanpa menambahkan styling eksternal liar.
3. **Deterministik & Zero-AI-Slop:** Tidak menggunakan AI generatif untuk soal/CP, 100% berakar pada Kepka BSKAP No. 046/H/KR/2025 dan dataset resmi.
4. **Approval Gate:** Menunggu persetujuan eksplisit pengguna sebelum memindahkan ke `todo/` dan menulis kode.
