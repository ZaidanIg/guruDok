# guruDok

Platform Otomasi Dokumen Administrasi Guru SD/SMP/SMA berbasis Template Deterministik (Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13/2025).

## Struktur Proyek
* `backend/` — FastAPI Python REST API + Engine Dokumen (`.docx`, `.xlsx`, `.pdf`) + PostgreSQL (`GuruDocDB`)
* `frontend/` — Vite + React + TypeScript + Tailwind CSS (Claymorphism UI)
* `document/` — Spesifikasi proyek, dataset BSKAP 2025, dan panduan deployment (`document/deployment-coolify-duckdns.md`)
* `docker-compose.staging.yml` — Konfigurasi Docker Compose untuk staging di Coolify + DuckDNS
