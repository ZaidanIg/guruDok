"""Test Dataset Readiness Gate (Sprint 33).

Mandatory Zero-Trust verification gate enforcing the 4 objective dataset parameters:
1. Zero synthetic chapters / generic placeholders.
2. 6 official religions present across all grades (SD, SMP, SMA).
3. No duplicate courses (e.g. SMA Kelas 10 Physics).
4. Total allocated JP of chapters strictly matches total_jp_intracurricular_year (Permendikdasmen 13/2025).
5. All courses achieve 100% verification score with verified status.
"""

import pytest
from app.core.database import get_db_manager

SYNTHETIC_PATTERNS = [
    "Konsep Dasar & Eksplorasi",
    "Analisis & Penerapan",
    "Pengembangan & Pemecahan Masalah",
    "Proyek Kontekstual & Evaluasi",
    "Aplikasi & Proyek Terpadu",
]

OFFICIAL_RELIGIONS = [
    "Islam",
    "Kristen",
    "Katolik",
    "Hindu",
    "Buddha",
    "Khonghucu",
]


def test_zero_synthetic_chapters_in_database():
    """P1: Every chapter in curriculum_chapters must be genuine SIBI/BSKAP, zero synthetic placeholders."""
    db = get_db_manager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chapter_id, course_id, chapter_title
                FROM curriculum_chapters
                WHERE chapter_title ILIKE '%Konsep Dasar & Eksplorasi%'
                   OR chapter_title ILIKE '%Analisis & Penerapan%'
                   OR chapter_title ILIKE '%Pengembangan & Pemecahan Masalah%'
                   OR chapter_title ILIKE '%Proyek Kontekstual & Evaluasi%'
                   OR chapter_title ILIKE '%Aplikasi & Proyek Terpadu%';
                """
            )
            rows = cur.fetchall()
            synthetic_count = len(rows)
            assert synthetic_count == 0, (
                f"Found {synthetic_count} synthetic placeholder chapters in GuruDocDB! "
                f"Samples: {[r['chapter_title'] for r in rows[:5]]}"
            )


def test_all_six_religions_present_across_grades():
    """All 6 official Indonesian religions must be distinct courses across SD (1-6), SMP (7-9), SMA (10-12)."""
    db = get_db_manager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Check SD Grades 1-6
            for grade in range(1, 7):
                cur.execute(
                    """
                    SELECT subject_name FROM curriculum_courses
                    WHERE education_level = 'SD' AND grade = %s AND subject_name ILIKE '%%Agama%%';
                    """,
                    (grade,),
                )
                subjects = [r["subject_name"] for r in cur.fetchall()]
                for rel in OFFICIAL_RELIGIONS:
                    assert any(rel.lower() in s.lower() for s in subjects), (
                        f"Missing Pendidikan Agama {rel} in SD Grade {grade}! Found: {subjects}"
                    )

            # Check SMP Grades 7-9
            for grade in range(7, 10):
                cur.execute(
                    """
                    SELECT subject_name FROM curriculum_courses
                    WHERE education_level = 'SMP' AND grade = %s AND subject_name ILIKE '%%Agama%%';
                    """,
                    (grade,),
                )
                subjects = [r["subject_name"] for r in cur.fetchall()]
                for rel in OFFICIAL_RELIGIONS:
                    assert any(rel.lower() in s.lower() for s in subjects), (
                        f"Missing Pendidikan Agama {rel} in SMP Grade {grade}! Found: {subjects}"
                    )

            # Check SMA Grades 10-12
            for grade in range(10, 13):
                cur.execute(
                    """
                    SELECT subject_name FROM curriculum_courses
                    WHERE education_level = 'SMA' AND grade = %s AND subject_name ILIKE '%%Agama%%';
                    """,
                    (grade,),
                )
                subjects = [r["subject_name"] for r in cur.fetchall()]
                for rel in OFFICIAL_RELIGIONS:
                    assert any(rel.lower() in s.lower() for s in subjects), (
                        f"Missing Pendidikan Agama {rel} in SMA Grade {grade}! Found: {subjects}"
                    )


def test_no_duplicate_courses():
    """No duplicate courses should exist for any education_level, grade, and subject_name."""
    db = get_db_manager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT education_level, grade, subject_name, COUNT(*) AS cnt
                FROM curriculum_courses
                GROUP BY education_level, grade, subject_name
                HAVING COUNT(*) > 1;
                """
            )
            duplicates = cur.fetchall()
            assert len(duplicates) == 0, f"Found duplicate courses: {duplicates}"


def test_jp_sum_matches_permendikdasmen_13_2025():
    """P2: Sum of chapter allocated_jp must exactly equal total_jp_intracurricular_year."""
    db = get_db_manager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.course_id, c.subject_name, c.education_level, c.grade,
                       c.total_jp_intracurricular_year,
                       COALESCE(SUM(ch.allocated_jp), 0) AS total_chapter_jp,
                       COUNT(ch.chapter_id) AS total_chapters
                FROM curriculum_courses c
                LEFT JOIN curriculum_chapters ch ON c.course_id = ch.course_id
                GROUP BY c.course_id, c.subject_name, c.education_level, c.grade, c.total_jp_intracurricular_year
                HAVING c.total_jp_intracurricular_year != COALESCE(SUM(ch.allocated_jp), 0);
                """
            )
            mismatches = cur.fetchall()
            assert len(mismatches) == 0, (
                f"Found {len(mismatches)} courses where chapter JP != total_jp_intracurricular_year! "
                f"Samples: {[{'course': m['course_id'], 'expected': m['total_jp_intracurricular_year'], 'actual': m['total_chapter_jp']} for m in mismatches[:5]]}"
            )


def test_all_courses_pass_readiness_threshold():
    """All courses in curriculum_courses must have verification_score = 100 and valid status."""
    db = get_db_manager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT course_id, subject_name, verification_status, verification_score
                FROM curriculum_courses
                WHERE verification_score < 100
                   OR verification_status NOT IN ('VERIFIED_SIBI', 'VERIFIED_BSKAP', 'TEMPLATE_FLEXIBLE');
                """
            )
            unready = cur.fetchall()
            assert len(unready) == 0, (
                f"Found {len(unready)} unverified courses! "
                f"Samples: {[{'course': u['course_id'], 'status': u['verification_status'], 'score': u['verification_score']} for u in unready[:5]]}"
            )
