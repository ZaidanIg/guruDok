# GuruDok Backend REST API

Backend engine resmi untuk platform otomasi administrasi guru Kurikulum Merdeka (Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13 Tahun 2025). Dibangun menggunakan **FastAPI**, **Object-Oriented Architecture (OOP)**, **Strategy & Factory Pattern**, dan pendekatan **Zero-Trust Security**.

---

## 1. Arsitektur Folder (Senior Backend Best Practice)

```text
backend/
├── app/
│   ├── main.py                  # Inisialisasi FastAPI, CORS, Middleware Keamanan & Exception Handlers
│   ├── core/                    # Konfigurasi, Security Guards, dan Exception Domain
│   │   ├── config.py            # Pydantic Settings & Environment Variables
│   │   ├── security.py          # InputSanitizer, PathTraversalGuard, FileAttackGuard (Zero-Trust)
│   │   └── exceptions.py        # Domain Exceptions & Custom HTTP Status Mapping
│   ├── models/                  # Domain Entities (OOP Data & Business Methods)
│   │   ├── curriculum.py        # CurriculumSubject, ChapterTopic, LearningObjective
│   │   ├── teacher.py           # TeacherProfile (Encapsulates KOP & Lembar Pengesahan)
│   │   └── document.py          # DocumentGenerationJob entity & status tracking
│   ├── schemas/                 # Strict Pydantic DTOs & Form Validators
│   │   ├── common.py            # Unified ApiResponse[T], ErrorResponse envelopes
│   │   ├── curriculum.py        # Enums (SD/SMP/SMA), SubjectResponse, ChapterResponse
│   │   ├── teacher.py           # TeacherProfileCreate (Strict regex, sanitasi nama, no_wa)
│   │   └── generation.py        # DocumentGenerateRequest & Response schemas
│   ├── repositories/            # Data Access Layer (Repository Pattern)
│   │   ├── base.py              # ICurriculumRepository, ITeacherRepository interfaces
│   │   ├── curriculum_repo.py   # JsonCurriculumRepository (In-memory indexed master BSKAP)
│   │   └── teacher_repo.py      # InMemoryTeacherRepository (Thread-safe profiles)
│   ├── services/                # Business Logic & Orchestration
│   │   ├── curriculum_service.py # Cascading dropdown logic & filter handler
│   │   ├── teacher_service.py    # Lead capture & profile synchronization
│   │   ├── storage_service.py    # IStorageService -> LocalStorageService / Cloudflare R2
│   │   ├── generation_service.py # Core orchestrator generation job
│   │   └── document_engine/      # Strategy Pattern Document Engines
│   │       ├── base_engine.py    # Abstract DocumentEngine (F4/A4 dimensions)
│   │       ├── docx_engine.py    # Word Generator (Modul Ajar, ATP, CP-TP, Prota)
│   │       ├── xlsx_engine.py    # Excel Generator (Promes 26 Minggu + Rumus SUM)
│   │       └── generator_factory.py # Factory Strategy selector
│   └── api/                     # REST API Controllers
│       ├── deps.py              # Dependency Injection providers
│       └── v1/
│           ├── api.py           # Aggregated APIRouter (/api/v1)
│           └── endpoints/       # Controller Endpoints (health, curriculum, teachers, generator, download)
├── tests/                       # Test Suite (TDD Pytest)
│   ├── test_security.py         # Test XSS, Path Traversal, File Attack Guard
│   ├── test_curriculum.py       # Test Master BSKAP 046/2025 Dataset indexing
│   ├── test_teachers.py         # Test Teacher Profile, KOP & Lembar Pengesahan
│   ├── test_document_engine.py  # Test Word (.docx) & Excel (.xlsx) output integrity
│   └── test_api_generator.py    # Test REST API integration & file downloads
├── pytest.ini                   # Pytest configuration & pythonpath
├── requirements.txt             # Locked Python packages
└── .env.example                 # Example environment variables
```

---

## 2. Prinsip Keamanan Zero-Trust & Perlindungan Form POST

Setiap endpoint tipe `POST` dilindungi secara berlapis:
1. **Sanitasi String & Anti-XSS (`InputSanitizer`)**:
   - Seluruh tag HTML (`<p>`, `<b>`, `<div>`, dll) dan tag berbahaya `<script>` otomatis dideteksi dan diblokir dengan `SecurityViolationError` (HTTP 400).
   - Null bytes (`\x00`) dibersihkan untuk mencegah bypass parser.
2. **Validasi Format Ketat (Whitelisting)**:
   - Nomor WhatsApp divalidasi ke standar penomoran Indonesia (`08...`, `+628...`) dan dinormalisasi otomatis ke E.164.
   - NIP guru dan kepala sekolah wajib 18 digit angka, 16 digit NUPTK, atau tanda `-` (guru honorer/swasta).
   - Batas jenjang dan kelas diverifikasi silang (contoh: SD hanya menerima kelas 1–6, SMP 7–9, SMA 10–12).
   - Input ID kurikulum diverifikasi ke database master BSKAP 046/2025; client tidak dapat menginjeksi kurikulum fiktif.
3. **Perlindungan Serangan Berkas (File Attack Protection)**:
   - **Batas Ukuran Payload (Max Body Size Limit)**: Middleware membatasi request body maksimum 2 MB untuk mencegah DoS/Resource Exhaustion.
   - **Path Traversal Guard**: Semua operasi file membersihkan karakter berbahaya (`..`, `/`, `\`, dll) dan memvalidasi jalur target berada dalam direktori izin.
   - **File Magic Byte / Signature Verification**: Berkas yang diunduh diverifikasi menggunakan signature ZIP (`PK\x03\x04`) bawaan Office Open XML, menolak file eksekusi atau polyglot berbahaya.

---

## 3. Menjalankan Server & Pengujian (TDD)

### Mengaktifkan Virtual Environment
```bash
# Masuk ke folder backend
cd backend

# Aktifkan virtual environment Windows
.\.venv\Scripts\Activate.ps1
```

### Menjalankan Seluruh Pengujian (Pytest)
```bash
pytest -v
```
*Hasil: 36/36 unit dan integration tests lolos (100% PASS).*

### Menjalankan Server API Lokal
```bash
uvicorn app.main:app --reload --port 8000
```
* Dokumentasi Swagger UI: `http://localhost:8000/docs`
* Dokumentasi ReDoc: `http://localhost:8000/redoc`
