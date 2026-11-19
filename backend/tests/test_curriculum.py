import pytest
from app.repositories.curriculum_repo import JsonCurriculumRepository
from app.models.curriculum import CurriculumSubject, ChapterTopic


@pytest.fixture
def repo():
    return JsonCurriculumRepository()


class TestCurriculumRepository:
    """Test suite for master curriculum repository."""

    def test_repo_initialization(self, repo: JsonCurriculumRepository):
        subjects = repo.get_subjects()
        assert len(subjects) > 0

    def test_filter_by_jenjang(self, repo: JsonCurriculumRepository):
        sd_subjects = repo.get_subjects(jenjang="SD")
        smp_subjects = repo.get_subjects(jenjang="SMP")
        sma_subjects = repo.get_subjects(jenjang="SMA")

        assert len(sd_subjects) > 0
        assert len(smp_subjects) > 0
        assert len(sma_subjects) > 0

        # Assert all SD subjects have jenjang == 'SD'
        for s in sd_subjects:
            assert s.jenjang == "SD"

    def test_filter_by_grade(self, repo: JsonCurriculumRepository):
        k7_subjects = repo.get_subjects(jenjang="SMP", kelas=7)
        assert len(k7_subjects) > 0
        for s in k7_subjects:
            assert s.kelas == 7

    def test_get_subject_by_id(self, repo: JsonCurriculumRepository):
        ipa_smp = repo.get_subject_by_id("SMP-K7-IPA")
        assert ipa_smp is not None
        assert ipa_smp.nama_mapel == "Ilmu Pengetahuan Alam (IPA)"
        assert ipa_smp.fase == "D"
        assert len(ipa_smp.bab_list) > 0

    def test_get_chapter_and_tp(self, repo: JsonCurriculumRepository):
        ch = repo.get_chapter("SMP-K7-IPA", "IPA-K7-B01")
        assert ch is not None
        assert "Hakikat" in ch.judul_bab
        assert len(ch.tujuan_pembelajaran) > 0
        assert ch.calculate_total_jp() > 0

    def test_get_profil_lulusan(self, repo: JsonCurriculumRepository):
        dpl = repo.get_profil_lulusan_dimensions()
        assert len(dpl) >= 6
        assert "Penalaran Kritis" in dpl
