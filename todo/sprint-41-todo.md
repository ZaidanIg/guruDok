# Sprint 41 ToDo — Pemisahan Tegas Bagian A (Pilihan Ganda) & Bagian B (Essai)

> **Status:** `VERIFIED_DONE`  
> **Target Branch:** `staging`  
> **Plan Reference:** [`plan/sprint-41-pemisahan-soal-pg-dan-essai-dua-bagian.md`](../plan/sprint-41-pemisahan-soal-pg-dan-essai-dua-bagian.md)

---

## Task Checklist

- [x] **Task 1: Perbaikan Sintaks & Refactor Dua Seksi Stacked di `QuestionBuilderSection.tsx`**
  - [x] Perbaiki error TS2322, TS17002, TS1005, TS2304 di `QuestionBuilderSection.tsx`.
  - [x] Bangun layout 2 kontainer stacked: Bagian A (Soal Pilihan Ganda) dan Bagian B (Soal Essai).
  - [x] Penomoran kartu independen: `PG #1..N` di Bagian A dan `Essai #1..M` di Bagian B.
  - [x] Tombol tambah mandiri: `+ Tambah Soal PG` di Bagian A, `+ Tambah Soal Essai` di Bagian B.
  - [x] Navigasi urutan kartu beroperasi di dalam lingkup bagian masing-masing.
  - [x] Kemampuan memindahkan soal antar bagian (Alih Tipe PG $\leftrightarrow$ Essai).
  - [x] Stimulus input tanpa label formal, teks textarea langsung dan bersih.

- [x] **Task 2: Tombol Tunggal Global Cerdas "Ambil dari Bank Soal"**
  - [x] Ambil kumpulan soal dari endpoint `GET /api/v1/questions`.
  - [x] Pemilahan otomatis: soal PG masuk ke Bagian A, soal Uraian masuk ke Bagian B.
  - [x] Notifikasi informatif kuota yang dimuat ke Bagian A dan Bagian B.

- [x] **Task 3: Live Document Preview `DocumentGenerator.tsx`**
  - [x] Header seksi naskah soal memuat `A. Soal Pilihan Ganda` dan `B. Soal Essai`.
  - [x] Penomoran butir soal direset per bagian: 1..N untuk PG dan 1..M untuk Essai.
  - [x] Stimulus polos sebagai paragraf biasa tanpa blok/kotak background dan tanpa kata "Stimulus".
  - [x] Penyelarasan nomor pada Tabel Kisi-Kisi dan Tabel Kunci Jawaban.

- [x] **Task 4: Sinkronisasi Backend Engine (`question_blueprint.py`, `docx_engine.py`, `pdf_engine.py`)**
  - [x] Pastikan blueprint menyertakan `pg_questions` (1..N) dan `essai_questions` (1..M).
  - [x] DOCX engine merender Bagian A & B dengan nomor `section_no`.
  - [x] PDF engine merender Bagian A & B dengan nomor `section_no` dan margin presisi.

- [x] **Task 5: Zero-Trust Verification & Automated Tests**
  - [x] Pytest suite lulus 100% (`backend/tests/` -> 122/122 passed).
  - [x] TypeScript build lulus tanpa error (`npm run build` -> 0 errors).

- [x] **Task 6: Git Commit & Push ke `staging`**
  - [x] Review diff bersih.
  - [x] Commit dan push ke `origin/staging`.
