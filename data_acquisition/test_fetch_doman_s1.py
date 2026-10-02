"""Tests that the Table S1 fetcher refuses anything that is not really a workbook.

Runs as a plain script, and also under pytest:

    python data_acquisition/test_fetch_doman_s1.py

Why this guard needs a test
---------------------------
The first version of the fetcher trusted HTTP 200 plus an `.xlsx` suffix, and it wrote six
files into `raw/` that were not workbooks at all. Both NCBI and the publisher answer a
scripted request for a supplementary binary with HTTP 200 and an HTML page: a bot check or
a cookie wall, a couple of kilobytes, served under the requested filename. Nothing about
the status code or the URL distinguishes that from the real file.

The consequence of accepting one is not a crash. It is `tasks/.../raw/mmc2.xlsx`
containing a Google reCAPTCHA page, with a recorded SHA256 and a provenance entry saying
it came from the publisher. Every later stage then reads a file that is not the table, and
the checksum makes the wrong file look pinned and verified.

So these tests are positive controls for refusal: each feeds something that is not a
workbook and asserts that the fetcher rejects it and says why.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import fetch_doman_s1 as fetcher  # noqa: E402

REAL_TABLE_S1 = REPO_ROOT / "tasks/taskA_crossfamily/raw/mmc2.xlsx"

# A trimmed copy of what NCBI actually served for mmc2.xlsx under HTTP 200.
BOT_CHECK_PAGE = (
    b"<!doctype html><html><head><title>Just a moment</title>"
    b"<script src='https://www.google.com/recaptcha/api.js'></script></head>"
    b"<body>Verifying you are human.</body></html>"
)


def test_rejects_an_html_bot_check_page() -> None:
    ok, why = fetcher.looks_like_xlsx(BOT_CHECK_PAGE)
    assert not ok, "an HTML bot-check page was accepted as a workbook"
    assert "not a zip container" in why, why


def test_rejects_an_empty_body() -> None:
    ok, why = fetcher.looks_like_xlsx(b"")
    assert not ok, "an empty body was accepted as a workbook"
    assert "fewer than 4 bytes" in why, why


def test_rejects_a_plain_zip_that_is_not_a_spreadsheet() -> None:
    """Zip magic alone must not be enough: a docx and a jar also start with PK."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("notes.txt", "this is a zip, but it is not a workbook")
    ok, why = fetcher.looks_like_xlsx(buffer.getvalue())
    assert not ok, "a plain zip was accepted as a workbook"
    assert "[Content_Types].xml" in why, why


def test_rejects_an_ooxml_package_that_is_not_a_spreadsheet() -> None:
    """A docx has the content types part but no xl/ tree, so it must still be refused."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    ok, why = fetcher.looks_like_xlsx(buffer.getvalue())
    assert not ok, "a word processing package was accepted as a spreadsheet"
    assert "not a spreadsheet package" in why, why


def test_rejects_zip_magic_with_a_corrupt_body() -> None:
    ok, why = fetcher.looks_like_xlsx(b"PK\x03\x04" + b"\x00" * 64)
    assert not ok, "a corrupt archive was accepted as a workbook"
    assert "unreadable" in why, why


def test_accepts_a_minimal_real_spreadsheet_package() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")
    ok, why = fetcher.looks_like_xlsx(buffer.getvalue())
    assert ok, "a valid spreadsheet package was refused: " + why


def test_accepts_the_acquired_table_s1_if_it_is_present() -> None:
    """The guard has to accept the real file, not merely reject everything."""
    if not REAL_TABLE_S1.is_file():
        print("    skipped: " + REAL_TABLE_S1.name + " is not present")
        return
    ok, why = fetcher.looks_like_xlsx(REAL_TABLE_S1.read_bytes())
    assert ok, "the acquired Table S1 was refused by its own guard: " + why


def main() -> int:
    tests = [
        test_rejects_an_html_bot_check_page,
        test_rejects_an_empty_body,
        test_rejects_a_plain_zip_that_is_not_a_spreadsheet,
        test_rejects_an_ooxml_package_that_is_not_a_spreadsheet,
        test_rejects_zip_magic_with_a_corrupt_body,
        test_accepts_a_minimal_real_spreadsheet_package,
        test_accepts_the_acquired_table_s1_if_it_is_present,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print("FAIL " + test.__name__ + ": " + str(error))
        except Exception as error:  # noqa: BLE001
            failures += 1
            print("ERROR " + test.__name__ + ": " + type(error).__name__ + ": " + str(error))
        else:
            print("pass " + test.__name__)
    print("tests: " + str(len(tests)) + ", failures: " + str(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
