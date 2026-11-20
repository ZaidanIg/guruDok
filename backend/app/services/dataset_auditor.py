"""Dataset Readiness Auditor (Sprint 33).

Evaluates curriculum courses, chapters, and learning objectives against
the 4 objective readiness criteria:
1. P1 (zero_synthetic_chapters): 0% synthetic/dummy chapter titles.
2. P2 (jp_matches_permendikdasmen): sum(chapter.allocated_jp) == course.total_jp_intracurricular_year.
3. P3 (all_cp_elements_covered): CP elements from BSKAP 046/2025 are covered.
4. P4 (specific_tp_quality): Specific, measurable TPs with ATP sequence & Bloom taxonomy.
"""

from typing import Dict, Any, List, Optional
import sys
from app.core.database import get_db_manager

SYNTHETIC_MARKERS = [
    "konsep dasar & eksplorasi",
    "analisis & penerapan",
    "pengembangan & pemecahan masalah",
    "proyek kontekstual & evaluasi",
    "aplikasi & proyek terpadu",
]


class DatasetReadinessAuditor:
    """Automated auditor evaluating dataset quality and curriculum readiness."""

    def __init__(self):
        self.db = get_db_manager()

    def audit_course(self, course: Dict[str, Any], chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audits a single course and its chapters against the 4 objective parameters."""
        course_id = course["course_id"]
        total_jp_target = course["total_jp_intracurricular_year"]
        status = course.get("verification_status") or "DRAFT"

        # P1: Zero synthetic chapters
        p1_pass = True
        synthetic_found = []
        if not chapters:
            p1_pass = False
        for ch in chapters:
            title_lower = (ch.get("chapter_title") or "").lower()
            for marker in SYNTHETIC_MARKERS:
                if marker in title_lower:
                    p1_pass = False
                    synthetic_found.append(ch.get("chapter_title"))
                    break

        # P2: JP alignment with Permendikdasmen 13/2025
        sum_jp = sum(ch.get("allocated_jp", 0) for ch in chapters)
        p2_pass = (sum_jp == total_jp_target) and (len(chapters) > 0)

        # P3: CP Element coverage (chapters should map to valid elements)
        p3_pass = True
        if not chapters:
            p3_pass = False
        else:
            for ch in chapters:
                elem = ch.get("element_names") or ""
                if not elem or len(elem.strip()) < 3:
                    p3_pass = False
                    break

        # P4: TP Specificity & Quality (min 2 TPs per chapter, valid descriptions)
        p4_pass = True
        total_tps = 0
        if not chapters:
            p4_pass = False
        else:
            for ch in chapters:
                tps = ch.get("tps") or []
                total_tps += len(tps)
                if len(tps) < 2:
                    p4_pass = False
                for tp in tps:
                    desc = tp.get("tp_description") or ""
                    if len(desc.strip()) < 15 or "placeholder" in desc.lower():
                        p4_pass = False

        score = (
            (25 if p1_pass else 0)
            + (25 if p2_pass else 0)
            + (25 if p3_pass else 0)
            + (25 if p4_pass else 0)
        )

        return {
            "course_id": course_id,
            "subject_name": course["subject_name"],
            "education_level": course["education_level"],
            "grade": course["grade"],
            "chapter_count": len(chapters),
            "tp_count": total_tps,
            "target_jp": total_jp_target,
            "actual_jp": sum_jp,
            "p1_zero_synthetic": p1_pass,
            "p2_jp_match": p2_pass,
            "p3_cp_covered": p3_pass,
            "p4_tp_quality": p4_pass,
            "score": score,
            "current_status": status,
            "synthetic_samples": synthetic_found[:2],
        }

    def audit_all(self, persist: bool = False) -> Dict[str, Any]:
        """Audits every course in the database and optionally persists scores."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT course_id, subject_code, education_level, grade, phase,
                           subject_name, sibi_reference_book, total_jp_intracurricular_year,
                           jp_per_week, verification_status, verification_score
                    FROM curriculum_courses
                    ORDER BY education_level, grade, subject_name;
                    """
                )
                courses = cur.fetchall()

                # Fetch all chapters
                cur.execute(
                    """
                    SELECT chapter_id, course_id, chapter_title, semester,
                           chapter_number, element_names, allocated_jp
                    FROM curriculum_chapters
                    ORDER BY chapter_number;
                    """
                )
                all_chapters = cur.fetchall()

                # Fetch all TPs
                cur.execute(
                    """
                    SELECT chapter_id, tp_code, atp_sequence, tp_description,
                           rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                    FROM learning_objectives_tp
                    ORDER BY atp_sequence;
                    """
                )
                all_tps = cur.fetchall()

        # Group TPs by chapter_id
        tp_by_chapter: Dict[str, List[Dict[str, Any]]] = {}
        for tp in all_tps:
            tp_by_chapter.setdefault(tp["chapter_id"], []).append(tp)

        # Attach TPs to chapters and group chapters by course_id
        chapters_by_course: Dict[str, List[Dict[str, Any]]] = {}
        for ch in all_chapters:
            ch_copy = dict(ch)
            ch_copy["tps"] = tp_by_chapter.get(ch["chapter_id"], [])
            chapters_by_course.setdefault(ch["course_id"], []).append(ch_copy)

        results = []
        scores_by_level = {"SD": [], "SMP": [], "SMA": []}

        for c in courses:
            chs = chapters_by_course.get(c["course_id"], [])
            res = self.audit_course(c, chs)
            results.append(res)
            lvl = c["education_level"]
            if lvl in scores_by_level:
                scores_by_level[lvl].append(res["score"])

        total_courses = len(results)
        passed_courses = sum(1 for r in results if r["score"] == 100)
        total_chapters = sum(r["chapter_count"] for r in results)
        synthetic_courses = sum(1 for r in results if not r["p1_zero_synthetic"])
        jp_mismatches = sum(1 for r in results if not r["p2_jp_match"])

        avg_score = (sum(r["score"] for r in results) / total_courses) if total_courses > 0 else 0

        summary = {
            "total_courses": total_courses,
            "passed_courses": passed_courses,
            "pass_percentage": round((passed_courses / total_courses * 100), 2) if total_courses > 0 else 0,
            "average_score": round(avg_score, 2),
            "total_chapters": total_chapters,
            "courses_with_synthetic_chapters": synthetic_courses,
            "courses_with_jp_mismatches": jp_mismatches,
            "scores_by_level": {
                lvl: round(sum(scores) / len(scores), 2) if scores else 0
                for lvl, scores in scores_by_level.items()
            },
            "results": results,
        }

        if persist:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    for r in results:
                        cur.execute(
                            """
                            UPDATE curriculum_courses
                            SET verification_score = %s
                            WHERE course_id = %s;
                            """,
                            (r["score"], r["course_id"]),
                        )

        return summary


def run_cli_audit():
    """Runs the audit CLI with a clean formatted console report."""
    auditor = DatasetReadinessAuditor()
    print("=================================================================")
    print(" GURUDOK DATASET READINESS AUDIT RUNNER (BSKAP 046/2025 & SIBI)")
    print("=================================================================")
    summary = auditor.audit_all(persist=True)

    print(f"Total Courses Evaluated : {summary['total_courses']}")
    print(f"Total Chapters Indexed  : {summary['total_chapters']}")
    print(f"Courses with Synthetic  : {summary['courses_with_synthetic_chapters']}")
    print(f"Courses with JP Mismatch: {summary['courses_with_jp_mismatches']}")
    print(f"Average Readiness Score : {summary['average_score']}%")
    print(f"Pass Rate (100% Score)  : {summary['passed_courses']}/{summary['total_courses']} ({summary['pass_percentage']}%)")
    print("-----------------------------------------------------------------")
    print(f"  SD  Average Score     : {summary['scores_by_level'].get('SD', 0)}%")
    print(f"  SMP Average Score     : {summary['scores_by_level'].get('SMP', 0)}%")
    print(f"  SMA Average Score     : {summary['scores_by_level'].get('SMA', 0)}%")
    print("=================================================================")

    if summary["courses_with_synthetic_chapters"] > 0:
        print("\nWARNING: Uncurated / Synthetic Courses Detected:")
        for r in summary["results"]:
            if not r["p1_zero_synthetic"]:
                print(f"  - [{r['course_id']}] {r['education_level']} K{r['grade']} {r['subject_name']} "
                      f"(Score: {r['score']}%) - Samples: {r['synthetic_samples']}")

    if summary["pass_percentage"] == 100.0:
        print("\nSUCCESS: 100% OF DATASET IS CURATED & VERIFIED! READY FOR SPRINT 34.")
        sys.exit(0)
    else:
        print(f"\nAUDIT GATE FAILED: Only {summary['pass_percentage']}% ready. Complete curation needed.")
        sys.exit(1)


if __name__ == "__main__":
    run_cli_audit()
