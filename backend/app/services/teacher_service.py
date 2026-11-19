from typing import Optional
from app.core.exceptions import ValidationError
from app.models.teacher import TeacherProfile
from app.repositories.base import ITeacherRepository
from app.schemas.teacher import TeacherProfileCreate, TeacherProfileResponse


class TeacherService:
    """Service managing Teacher leads, school data persistence, and profile verification."""

    def __init__(self, repo: ITeacherRepository):
        self.repo = repo

    def register_or_update(self, data: TeacherProfileCreate) -> TeacherProfileResponse:
        # Check if teacher phone exists
        existing = self.repo.find_by_phone(data.no_whatsapp)
        if existing:
            # Update fields
            existing.nama_guru = data.nama_guru
            existing.nip_guru = data.nip_guru
            existing.nama_sekolah = data.nama_sekolah
            existing.npsn = data.npsn
            existing.kabupaten_kota = data.kabupaten_kota
            existing.provinsi = data.provinsi
            existing.nama_kepala_sekolah = data.nama_kepala_sekolah
            existing.nip_kepala_sekolah = data.nip_kepala_sekolah
            existing.email = data.email
            existing.ukuran_kertas_default = data.ukuran_kertas_default.value
            saved = self.repo.save(existing)
        else:
            new_profile = TeacherProfile(
                nama_guru=data.nama_guru,
                nip_guru=data.nip_guru,
                nama_sekolah=data.nama_sekolah,
                npsn=data.npsn,
                kabupaten_kota=data.kabupaten_kota,
                provinsi=data.provinsi,
                nama_kepala_sekolah=data.nama_kepala_sekolah,
                nip_kepala_sekolah=data.nip_kepala_sekolah,
                no_whatsapp=data.no_whatsapp,
                email=data.email,
                ukuran_kertas_default=data.ukuran_kertas_default.value,
            )
            saved = self.repo.save(new_profile)

        return self._to_response(saved)

    def get_by_id(self, profile_id: str) -> Optional[TeacherProfileResponse]:
        profile = self.repo.find_by_id(profile_id)
        if not profile:
            return None
        return self._to_response(profile)

    def get_entity_by_id(self, profile_id: str) -> Optional[TeacherProfile]:
        return self.repo.find_by_id(profile_id)

    def _to_response(self, profile: TeacherProfile) -> TeacherProfileResponse:
        return TeacherProfileResponse(
            id=profile.id,
            nama_guru=profile.nama_guru,
            nip_guru=profile.nip_guru,
            nama_sekolah=profile.nama_sekolah,
            npsn=profile.npsn,
            kabupaten_kota=profile.kabupaten_kota,
            provinsi=profile.provinsi,
            nama_kepala_sekolah=profile.nama_kepala_sekolah,
            nip_kepala_sekolah=profile.nip_kepala_sekolah,
            no_whatsapp=profile.no_whatsapp,
            email=profile.email,
            ukuran_kertas_default=profile.ukuran_kertas_default,
            created_at=profile.created_at.isoformat(),
        )
