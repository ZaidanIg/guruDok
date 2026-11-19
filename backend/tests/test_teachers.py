import pytest
from app.models.teacher import TeacherProfile
from app.repositories.teacher_repo import InMemoryTeacherRepository
from app.schemas.teacher import TeacherProfileCreate
from pydantic import ValidationError


class TestTeacherModule:
    """Test suite for teacher profile entity, validation schemas, and repository."""

    def test_create_valid_teacher_profile(self):
        schema = TeacherProfileCreate(
            nama_guru="Siti Aminah, S.Pd.",
            nip_guru="198805122014022003",
            nama_sekolah="SMP Negeri 1 Surabaya",
            kabupaten_kota="Kota Surabaya",
            provinsi="Jawa Timur",
            nama_kepala_sekolah="Drs. H. Bambang Irawan, M.Pd.",
            nip_kepala_sekolah="196904151995121002",
            no_whatsapp="081234567890",
            ukuran_kertas_default="F4",
        )
        assert schema.nama_guru == "Siti Aminah, S.Pd."
        assert schema.no_whatsapp == "+6281234567890"  # Normalized to E.164

    def test_reject_xss_in_teacher_name(self):
        with pytest.raises(Exception):
            TeacherProfileCreate(
                nama_guru="<script>alert('hack')</script> Budi",
                nip_guru="-",
                nama_sekolah="SDN 1",
                kabupaten_kota="Bandung",
                provinsi="Jawa Barat",
                nama_kepala_sekolah="Kasek",
                nip_kepala_sekolah="-",
                no_whatsapp="081234567890",
            )

    def test_teacher_repository_crud(self):
        repo = InMemoryTeacherRepository()
        profile = TeacherProfile(
            nama_guru="Ahmad Fauzi, M.Pd.",
            nip_guru="198001012005011001",
            nama_sekolah="SMA Negeri 3 Bandung",
            kabupaten_kota="Kota Bandung",
            provinsi="Jawa Barat",
            nama_kepala_sekolah="Dr. Hj. Nurjanah, M.Pd.",
            nip_kepala_sekolah="197502022000032001",
            no_whatsapp="+6281987654321",
        )

        saved = repo.save(profile)
        assert saved.id == profile.id

        # Find by ID
        found_by_id = repo.find_by_id(saved.id)
        assert found_by_id is not None
        assert found_by_id.nama_guru == "Ahmad Fauzi, M.Pd."

        # Find by phone
        found_by_phone = repo.find_by_phone("+6281987654321")
        assert found_by_phone is not None
        assert found_by_phone.nama_sekolah == "SMA Negeri 3 Bandung"

    def test_kop_and_lembar_pengesahan_formatting(self):
        profile = TeacherProfile(
            nama_guru="Siti Aminah, S.Pd.",
            nip_guru="198805122014022003",
            nama_sekolah="SMP Negeri 1 Surabaya",
            kabupaten_kota="Kota Surabaya",
            provinsi="Jawa Timur",
            nama_kepala_sekolah="Drs. H. Bambang Irawan, M.Pd.",
            nip_kepala_sekolah="196904151995121002",
            no_whatsapp="+6281234567890",
        )

        kop = profile.get_formatted_kop()
        assert kop["nama_sekolah"] == "SMP NEGERI 1 SURABAYA"
        assert kop["nama_guru"] == "Siti Aminah, S.Pd."

        pengesahan = profile.get_lembar_pengesahan(tanggal_pengesahan="15 Juli 2026")
        assert "Surabaya, 15 Juli 2026" in pengesahan["titimangsa"]
        assert pengesahan["nama_kepala_sekolah"] == "Drs. H. Bambang Irawan, M.Pd."
        assert "198805122014022003" in pengesahan["nip_guru"]
