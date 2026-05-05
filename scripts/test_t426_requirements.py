from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup

from refresh_t426 import (
    ROOT,
    INDEX_PATH,
    VIDEO_MP4,
    ABOUT_TEXT_1,
    ABOUT_TEXT_2,
    GALLERY_TEXTS,
    HOT_ROWS,
    INTERNSHIP_FILES,
    split_docx_sections,
    INTERNSHIP_DIR,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_index_content() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    assert_true(ABOUT_TEXT_1 in html, "Thiếu text cập nhật mục 'CHÚNG TÔI LÀ...'")
    assert_true(ABOUT_TEXT_2 in html, "Thiếu text cập nhật mục 'ĐỊNH HƯỚNG NGHỀ NGHIỆP'")

    video = soup.select_one("video.video-local-player")
    assert_true(video is not None, "Không tìm thấy video player local")
    sources = [source.get("src", "") for source in video.select("source")]
    assert_true("assets/videos/YEP_VNPT_Fintech.mp4" in sources, "Thiếu source mp4 cho video")
    assert_true(VIDEO_MP4.exists(), "Thiếu file mp4 sau khi chuyển mã video")
    speed_select = soup.select_one("#video-speed-select")
    assert_true(speed_select is not None, "Thiếu control chỉnh tốc độ phát")
    options = [opt.get("value", "") for opt in speed_select.select("option")]
    assert_true(options == ["0.75", "1", "1.25", "1.5", "2"], f"Sai danh sách tốc độ phát: {options}")
    assert_true("VIDEO FIN TẾT 2026" not in html, "Vẫn còn chữ VIDEO FIN TẾT 2026 trên giao diện")

    creation_cards = soup.select("#creation .creation-card")
    assert_true(len(creation_cards) == 5, f"Sai số lượng ảnh gallery, mong đợi 5, thực tế {len(creation_cards)}")
    assert_true("creation-card--hero" in creation_cards[0].get("class", []), "Ảnh đầu chưa được đặt ở hàng 1 kiểu hero")
    for index, text in enumerate(GALLERY_TEXTS):
        attr_text = creation_cards[index].get("data-creation-text", "")
        assert_true(attr_text == text, f"Sai text overlay ảnh thứ {index + 1}")
    keep_phrases = [node.get_text(strip=True) for node in soup.select("#creation .keep-phrase")]
    for phrase in [
        "SÁNG TẠO - TIÊN PHONG",
        '"QUẨY" HẾT MÌNH',
        '"CÀY" NHIỆT TÌNH',
        '"GẠO NGON"',
        "THÍCH LÀ NHÍCH",
        "XÍCH GẦN NHAU",
    ]:
        assert_true(phrase in keep_phrases, f"Thiếu keep-phrase cho cụm: {phrase}")

    career_titles = [node.get_text(strip=True) for node in soup.select(".career-table-title")]
    assert_true("TUYỂN DỤNG NÓNG" in career_titles, "Thiếu bảng TUYỂN DỤNG NÓNG")
    assert_true("TUYỂN DỤNG THỰC TẬP SINH/ HỌC VIỆC" in career_titles, "Thiếu bảng TUYỂN DỤNG THỰC TẬP SINH/ HỌC VIỆC")

    for href, title, _ in HOT_ROWS:
        link = soup.select_one(f'a[href="{href}"]')
        assert_true(link is not None, f"Thiếu link hot job: {href}")
        assert_true(link.get_text(strip=True) == title, f"Sai title hot job cho {href}")

    for meta in INTERNSHIP_FILES:
        link = soup.select_one(f'a[href="{meta.slug}"]')
        assert_true(link is not None, f"Thiếu link internship: {meta.slug}")
        assert_true(link.get_text(strip=True) == meta.title_short, f"Sai title internship cho {meta.slug}")

    assert_true("TUY?N D?NG" not in html, "Index vẫn còn lỗi font tiếng Việt ở bảng tuyển dụng")


def test_internship_pages() -> None:
    for meta in INTERNSHIP_FILES:
        page_path = ROOT / meta.slug
        assert_true(page_path.exists(), f"Thiếu file internship page: {meta.slug}")
        html = page_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one(".header-title")
        assert_true(title_node is not None, f"Thiếu header-title tại {meta.slug}")
        assert_true(title_node.get_text(strip=True) == meta.title_short, f"Sai tiêu đề trang tại {meta.slug}")

        about, desc, req, benefits = split_docx_sections(INTERNSHIP_DIR / meta.source_name)
        assert_true(about in html, f"Thiếu đoạn giới thiệu từ docx tại {meta.slug}")
        assert_true(any(item in html for item in desc[:3]), f"Thiếu nội dung mô tả chính từ docx tại {meta.slug}")
        assert_true(any(item in html for item in req[:3]), f"Thiếu nội dung yêu cầu chính từ docx tại {meta.slug}")
        assert_true(any(item in html for item in benefits[:2]), f"Thiếu nội dung quyền lợi chính từ docx tại {meta.slug}")
        assert_true("Th?c t?p sinh" not in html, f"Trang {meta.slug} vẫn còn lỗi font tiếng Việt")


def main() -> None:
    test_index_content()
    test_internship_pages()
    print("test_t426_requirements: ok")


if __name__ == "__main__":
    main()
