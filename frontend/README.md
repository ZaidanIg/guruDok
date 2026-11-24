# GuruDok Frontend (Vite + React + TypeScript + Tailwind CSS Claymorphism)

Antarmuka web responsif (Desktop & Mobile) untuk platform otomasi administrasi guru **GuruDok.guru**, dibangun dengan gaya visual **Claymorphism (Soft 3D Tactile)** sesuai referensi desain resmi di folder `asset/`.

---

## 1. Struktur Folder Frontend

```text
frontend/
├── public/
│   └── hero-clay-3d.png                # Maskot 3D Clay resolusi tinggi (Topi Toga, Word & Excel)
├── src/
│   ├── types/
│   │   └── index.ts                    # Kontrak TypeScript (selaras dengan Pydantic schema Backend)
│   ├── constants/
│   │   └── services.ts                 # Katalog 5 Service Inti MVP + Roadmap 13 Service Tambahan
│   ├── services/
│   │   ├── api.ts                      # Modular OOP API Client (GuruDokApiClient)
│   │   └── fallbackData.ts             # Dataset BSKAP 046/2025 fallback jika backend belum dinyalakan
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx              # Floating Clay Navbar + Pill Profil Guru
│   │   │   ├── BottomNav.tsx           # Mobile Floating Clay Bottom Navigation
│   │   │   └── Footer.tsx              # Clay Footer & Badge Regulasi BSKAP 046/2025
│   │   ├── sections/
│   │   │   ├── HeroSection.tsx         # Hero Banner + 3 Feature Badges + 3D Clay Illustration Card
│   │   │   ├── QuickFilterBar.tsx      # Filter Cepat Jenjang, Kelas & Pencarian
│   │   │   ├── ServiceCatalog.tsx      # Grid 3x2 Katalog 5 Service Utama + Modal Roadmap 18 Service
│   │   │   ├── DocumentGenerator.tsx   # Generator 2 Kolom (Step 1: Cascading Form & Step 2: Auto-Preview)
│   │   │   └── DocumentHistory.tsx     # Tabel & Kartu Riwayat "Berkas Administrasi Saya"
│   │   └── modals/
│   │       ├── SchoolProfileModal.tsx  # Modal "Lengkapi Profil Sekolah Anda" (KOP & Lembar Pengesahan)
│   │       └── SuccessDownloadModal.tsx # Modal "Dokumen Berhasil Dibuat!" + Download & Share WA
│   ├── App.tsx                         # Orkestrasi State Utama & Integrasi API
│   ├── main.tsx                        # React Entrypoint
│   └── index.css                       # Design System Claymorphism (.clay-card, .clay-input, .clay-btn-primary)
├── index.html                          # Google Fonts (Plus Jakarta Sans) & SEO Meta
├── tailwind.config.js                  # Konfigurasi Shadow & Font Claymorphism
└── vite.config.ts                      # Proxy otomatis `/api` -> `http://localhost:8000`
```

---

## 2. Cara Menjalankan Frontend & Backend Bersamaan

### Terminal 1 — Menjalankan Backend (FastAPI Port 8000)
```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Terminal 2 — Menjalankan Frontend (Vite Port 5173)
```powershell
cd frontend
npm.cmd run dev
```

Buka browser di **`http://localhost:5173`**. Seluruh request ke `/api/v1/*` otomatis diteruskan oleh Vite Proxy ke backend FastAPI di `http://localhost:8000`.
