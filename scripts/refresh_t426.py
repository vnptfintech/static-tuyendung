from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import html
import re
import subprocess
from typing import Iterable

from docx import Document
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.html"
UPDATE_DIR = ROOT / "update_tuyendung"
VIDEO_MOV = ROOT / "assets" / "videos" / "YEP_VNPT_Fintech.mov"
VIDEO_MP4 = ROOT / "assets" / "videos" / "YEP_VNPT_Fintech.mp4"


def find_internship_dir() -> Path:
    matches = sorted(path for path in UPDATE_DIR.glob("Th*") if path.is_dir())
    if not matches:
        raise FileNotFoundError(f"Không tìm thấy thư mục internship nguồn trong {UPDATE_DIR}")
    return matches[0]


INTERNSHIP_DIR = find_internship_dir()


ABOUT_TEXT_1 = (
    "VNPT FinTech là đơn vị TIÊN PHONG được Tập đoàn Bưu Chính Viễn Thông Việt Nam (VNPT) "
    "giao nhiệm vụ triển khai và vận hành các dịch vụ tài chính số và được Ngân hàng Nhà nước "
    "cấp giấy phép cung ứng dịch vụ trung gian thanh toán. Tham gia vào VNPT FinTech đồng nghĩa "
    "với việc bạn sẽ tham gia vào 1 môi trường SỐ HOÁ và trở thành 1 thành viên của đại gia đình VNPT."
)

ABOUT_TEXT_2 = (
    "FinTech đang được xếp vào TOP các nhóm ngành nghề triển vọng tại Việt Nam và là hệ sinh thái "
    "dịch vụ được VNPT đầu tư, chú trọng, quyết tâm có những đột phá trên thị trường. Vậy tại sao "
    "bạn lại không thử sức mình trong 1 lĩnh vực đầy tính thách thức nhưng cũng nhiều cơ hội phát "
    "triển như vậy bằng cách gia nhập Trung tâm dịch vụ tài chính số VNPT FinTech."
)

ABOUT_TEXT_3 = (
    'VNPT Money là sản phẩm tiêu biểu của VNPT FinTech tại thời điểm hiện tại. VNPT Money là hệ '
    'sinh thái thanh toán số qua ví điện tử, thẻ nội địa, thẻ quốc tế...đáp ứng nhu cầu thanh toán '
    'tiện lợi, an toàn và nhanh chóng cho hầu hết các nhu cầu hàng ngày: nạp thẻ cào, cước di động, '
    'truyền hình, internet; điện, nước, mua vé xem phim, vé máy bay, bảo hiểm…Bạn có thể bật Google '
    'và search "VNPT Money" để xem mọi người nói gì về sản phẩm này nhé!'
)

GALLERY_TEXTS = [
    "NƠI MÀ CHÚNG TÔI MỖI NGƯỜI MỘT CÁ TÍNH NHƯNG ĐỀU QUYẾT LIỆT - DỨT KHOÁT",
    "NƠI MÀ SÁNG TẠO - TIÊN PHONG LUÔN ĐẶT LÊN HÀNG ĐẦU",
    'NƠI MÀ CHÚNG TÔI "QUẨY" HẾT MÌNH - "CÀY" NHIỆT TÌNH',
    'NƠI MÀ CHÚNG TÔI CỨ "SÁNG TẠO" ẮT CÓ "GẠO NGON"',
    "NƠI MÀ CHÚNG TÔI THÍCH LÀ NHÍCH - XÍCH GẦN NHAU",
]

GALLERY_HTML = [
    'NƠI MÀ CHÚNG TÔI <span class="keep-phrase">MỖI NGƯỜI MỘT CÁ TÍNH</span> NHƯNG ĐỀU <span class="keep-phrase">QUYẾT LIỆT - DỨT KHOÁT</span>',
    'NƠI MÀ <span class="keep-phrase">SÁNG TẠO - TIÊN PHONG</span> LUÔN ĐẶT LÊN HÀNG ĐẦU',
    'NƠI MÀ CHÚNG TÔI <span class="keep-phrase">"QUẨY" HẾT MÌNH</span> - <span class="keep-phrase">"CÀY" NHIỆT TÌNH</span>',
    'NƠI MÀ CHÚNG TÔI CỨ <span class="keep-phrase">"SÁNG TẠO"</span> ẮT CÓ <span class="keep-phrase">"GẠO NGON"</span>',
    'NƠI MÀ CHÚNG TÔI <span class="keep-phrase">THÍCH LÀ NHÍCH</span> - <span class="keep-phrase">XÍCH GẦN NHAU</span>',
]


HOT_ROWS = [
    ("software-operation.html", "Chuyên viên Vận hành Phần mềm (Software Operation)", "- - -"),
    ("admin-assistant.html", "Nhân viên hành chính", "3/5/2026"),
    ("gift-design-specialist.html", "Chuyên viên Thiết kế quà tặng", "3/5/2026"),
    ("enterprise-customer-service.html", "Chuyên viên Dịch vụ Khách hàng Doanh nghiệp", "3/5/2026"),
    ("international-sales-support.html", "Nhân viên Hỗ trợ Kinh doanh Quốc tế", "30/04/2026"),
    ("kscl.html", "Kiểm soát chất lượng", "Đang mở"),
    ("ptnv.html", "Phân tích nghiệp vụ", "Đang mở"),
    ("ptgp.html", "Phát triển Giải pháp", "Đang mở"),
    ("ds.html", "Đối soát", "Đang mở"),
    ("bd.html", "Biller merchant", "Đang mở"),
    ("ptsp.html", "Thiết kế UI / UX", "Đang mở"),
    ("bd1.html", "Phát triển kinh doanh (BD) - phát triển merchant chấp nhận thanh toán tại điểm", "Đang mở"),
    ("dfs.html", "Kinh doanh dịch vụ tài chính số (DFS) phụ trách mảng hợp tác ngân hàng, tổ chức tài chính", "Đang mở"),
    ("dfsb2c.html", "Kinh doanh dịch vụ tài chính số (DFS) phụ trách mảng kinh doanh B2C", "Đang mở"),
    ("dfsnew.html", "Kinh doanh dịch vụ tài chính số (DFS) phụ trách mảng dịch vụ mới", "Đang mở"),
    ("po.html", "Phát triển sản phẩm (PO)", "Đang mở"),
    ("ptdl.html", "Phân tích dữ liệu", "Đang mở"),
    ("ksqtht.html", "Quản trị hệ thống", "Đang mở"),
    ("ksantt.html", "An ninh thông tin", "Đang mở"),
    ("cvtt.html", "Truyền thông", "Đang mở"),
    ("cvqtrr.html", "Quản trị rủi ro", "Đang mở"),
    ("cvksnb.html", "Kiểm soát nội bộ", "Đang mở"),
    ("nvcskh.html", "Chăm sóc khách hàng", "Đang mở"),
]


@dataclass(frozen=True)
class InternshipMeta:
    source_name: str
    slug: str
    department: str
    title_short: str


INTERNSHIP_FILES = [
    InternshipMeta("JD-ANTT.docx", "intern-antt.html", "An ninh thông tin", "Thực tập sinh An ninh thông tin"),
    InternshipMeta("JD-PTDL.docx", "intern-ptdl.html", "Phân tích dữ liệu", "Thực tập sinh Phân tích dữ liệu"),
    InternshipMeta("JD-PTPS-PO Intern.docx", "intern-po.html", "Phát triển sản phẩm", "Thực tập sinh Phát triển sản phẩm (PO)"),
    InternshipMeta("JD-PTSP-BA Intern.docx", "intern-ba.html", "Phân tích nghiệp vụ", "Thực tập sinh Phân tích nghiệp vụ (BA)"),
    InternshipMeta("JD-PTSP-DEV Intern.docx", "intern-dev.html", "Phát triển giải pháp", "Thực tập sinh Lập trình viên (DEV)"),
    InternshipMeta("JD-PTSP-QA Intern.docx", "intern-qa.html", "Kiểm thử phần mềm", "Thực tập sinh Kiểm thử phần mềm (QA)"),
    InternshipMeta("JD-PTSP-UXUI Intern.docx", "intern-uxui.html", "Thiết kế UI/UX", "Thực tập sinh Thiết kế giao diện (UX/UI)"),
    InternshipMeta("JD-QTHT.docx", "intern-system.html", "Quản trị hệ thống", "Thực tập sinh Quản trị hệ thống"),
]


def clean_text(value: str) -> str:
    return " ".join(value.split()).strip()


def make_rows(rows: Iterable[tuple[str, str, str]]) -> str:
    rendered = []
    for href, title, deadline in rows:
        rendered.append(
            "                <tr>\n"
            f'                  <td><a href="{href}">{html.escape(title)}</a></td>\n'
            f"                  <td>{html.escape(deadline)}</td>\n"
            "                </tr>"
        )
    return "\n".join(rendered)


def transcode_video() -> None:
    if VIDEO_MP4.exists() and VIDEO_MP4.stat().st_size > 0:
        return

    if not VIDEO_MOV.exists():
        raise FileNotFoundError(
            f"Thiếu video nguồn để tạo MP4: {VIDEO_MOV}. Hãy giữ file MP4 đã tối ưu hoặc cung cấp lại file MOV nguồn."
        )

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(VIDEO_MOV),
        "-vf",
        "scale='min(1920,iw)':-2",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(VIDEO_MP4),
    ]
    subprocess.run(cmd, check=True)


def render_about_section() -> str:
    return f"""    <section id="about" class="about-area">
      <div class="container">
        <div class="row">
          <div class="col-lg-6">
            <div class="section-title pb-10">
              <h4 class="title">VỀ CHÚNG TÔI</h4>
            </div>
          </div>
        </div>
        <div class="row">
          <div class="col-xl-6">
            <div class="about-content d-sm-flex">
              <div class="about-icon">
                <i class="lni-users"></i>
              </div>
              <div class="about-content media-body">
                <h4 class="about-title">CHÚNG TÔI LÀ...</h4>
                <p class="text">{html.escape(ABOUT_TEXT_1)}</p>
              </div>
            </div>
            <div class="about-content d-sm-flex">
              <div class="about-icon">
                <i class="lni-stats-up"></i>
              </div>
              <div class="about-content media-body">
                <h4 class="about-title">ĐỊNH HƯỚNG NGHỀ NGHIỆP</h4>
                <p class="text">{html.escape(ABOUT_TEXT_2)}</p>
              </div>
            </div>
            <div class="about-content d-sm-flex">
              <div class="about-icon">
                <i class="lni-brush"></i>
              </div>
              <div class="about-content media-body">
                <h4 class="about-title">VNPT MONEY LÀ...</h4>
                <p class="text">{html.escape(ABOUT_TEXT_3)}</p>
              </div>
            </div>
          </div>
          <div class="col-xl-6">
            <div class="about-video d-lg-flex align-items-center">
              <div class="video video-local-wrap">
                <video class="video-local-player" controls preload="metadata" playsinline>
                  <source src="assets/videos/YEP_VNPT_Fintech.mp4" type="video/mp4">
                  Trình duyệt của bạn không hỗ trợ phát video nội bộ. <a href="assets/videos/YEP_VNPT_Fintech.mp4">Mở video</a>
                </video>
                <div class="video-tools">
                  <label class="video-speed-label" for="video-speed-select">Tốc độ</label>
                  <select id="video-speed-select" class="video-speed-select">
                    <option value="0.75">0.75x</option>
                    <option value="1" selected>1x</option>
                    <option value="1.25">1.25x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>"""


def render_creation_section() -> str:
    buttons = []
    for index, text in enumerate(GALLERY_TEXTS, start=1):
        hero_class = " creation-card--hero" if index == 1 else ""
        active_class = " is-active" if index == 1 else ""
        buttons.append(
            f'          <button class="creation-card{hero_class}{active_class}" type="button" '
            f'data-creation-card data-creation-text="{html.escape(text)}">\n'
            f'            <img src="assets/images/creation-gallery-{index}.png" alt="VNPT FinTech gallery {index}">\n'
            '            <span class="creation-card-overlay">\n'
            f'              <span class="creation-card-text">{GALLERY_HTML[index - 1]}</span>\n'
            "            </span>\n"
            "          </button>"
        )

    return (
        """    <section id="creation" class="creation-area creation-gallery-area">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-lg-8">
            <div class="section-title text-center pb-10">
              <h4 class="title">SÁNG TẠO VÀ GẮN KẾT</h4>
            </div>
            <p class="creation-gallery-note text-center">Click vào từng ảnh để xem tinh thần văn hoá nổi bật của đội ngũ VNPT FinTech.</p>
          </div>
        </div>
        <div class="creation-gallery-grid creation-gallery-grid--updated">
"""
        + "\n".join(buttons)
        + """
        </div>
      </div>
    </section>"""
    )


def render_forte_section() -> str:
    internship_rows = [(meta.slug, meta.title_short, "Đang mở") for meta in INTERNSHIP_FILES]
    return f"""    <section id="forte" class="forte-area career-tables-area">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-lg-8">
            <div class="section-title text-center pb-10">
              <h4 class="title">THAM GIA CÙNG CHÚNG TÔI</h4>
            </div>
            <p class="career-table-intro text-center">Các vị trí bên dưới được trình bày theo dạng bảng để bạn tra cứu nhanh và đi thẳng tới trang mô tả chi tiết.</p>
          </div>
        </div>

        <div class="career-table-card">
          <h5 class="career-table-title">TUYỂN DỤNG NÓNG</h5>
          <div class="table-responsive">
            <table class="career-table">
              <thead>
                <tr>
                  <th>Công việc</th>
                  <th>Ngày hết hạn</th>
                </tr>
              </thead>
              <tbody>
{make_rows(HOT_ROWS)}
              </tbody>
            </table>
          </div>
        </div>

        <div class="career-table-card">
          <h5 class="career-table-title">TUYỂN DỤNG THỰC TẬP SINH/ HỌC VIỆC</h5>
          <div class="table-responsive">
            <table class="career-table">
              <thead>
                <tr>
                  <th>Công việc</th>
                  <th>Ngày hết hạn</th>
                </tr>
              </thead>
              <tbody>
{make_rows(internship_rows)}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>"""


def replace_section(text: str, section_id: str, replacement: str) -> str:
    pattern = re.compile(rf'    <section id="{section_id}".*?</section>', re.S)
    return pattern.sub(replacement, text, count=1)


def strip_cloudflare_beacon(text: str) -> str:
    return re.sub(
        r'\n?\s*<script\s+defer\s+src="https://static\.cloudflareinsights\.com/beacon\.min\.js[^>]*></script>\s*',
        '\n',
        text,
        flags=re.I,
    )


def refresh_index() -> None:
    text = INDEX_PATH.read_text(encoding="utf-8")
    text = replace_section(text, "about", render_about_section())
    text = replace_section(text, "creation", render_creation_section())
    text = replace_section(text, "forte", render_forte_section())
    text = re.sub(
        r"    <script>\s*\(function \(\) \{.*?</script>",
        """    <script>
      (function () {
        var cards = document.querySelectorAll('[data-creation-card]');
        cards.forEach(function (card) {
          card.addEventListener('click', function () {
            cards.forEach(function (item) {
              item.classList.remove('is-active');
            });
            card.classList.add('is-active');
          });
        });

        var video = document.querySelector('.video-local-player');
        var speedSelect = document.getElementById('video-speed-select');
        if (video) {
          var seekInitialFrame = function () {
            if (video.duration && video.duration > 1 && video.currentTime < 0.95) {
              try {
                video.currentTime = 1;
              } catch (error) {
                // Ignore browsers that block early seek until metadata is ready.
              }
            }
          };

          video.addEventListener('loadedmetadata', seekInitialFrame, { once: true });
          if (video.readyState >= 1) {
            seekInitialFrame();
          }
        }

        if (video && speedSelect) {
          speedSelect.addEventListener('change', function () {
            video.playbackRate = Number(speedSelect.value || '1');
          });
        }
      })();
    </script>""",
        text,
        count=1,
        flags=re.S,
    )
    text = strip_cloudflare_beacon(text)
    INDEX_PATH.write_text(text, encoding="utf-8")


def split_docx_sections(docx_path: Path) -> tuple[str, list[str], list[str], list[str]]:
    paragraphs = [clean_text(p.text) for p in Document(str(docx_path)).paragraphs]
    paragraphs = [p for p in paragraphs if p]

    about = ""
    desc: list[str] = []
    req: list[str] = []
    benefits: list[str] = []
    target = None

    for paragraph in paragraphs:
        upper = paragraph.upper()
        if upper.startswith("VỀ VNPT FINTECH"):
            target = "about"
            continue
        if "I. MÔ TẢ CÔNG VIỆC" in upper:
            target = "desc"
            continue
        if "II. YÊU CẦU ỨNG VIÊN" in upper:
            target = "req"
            continue
        if "III. QUYỀN LỢI" in upper:
            target = "benefits"
            continue

        if target == "about" and not about:
            about = paragraph
        elif target == "desc":
            desc.append(paragraph)
        elif target == "req":
            req.append(paragraph)
        elif target == "benefits":
            benefits.append(paragraph)

    return about, desc, req, benefits


def render_list(items: Iterable[str]) -> str:
    return "\n".join(f"                      <li>{html.escape(item)}</li>" for item in items)


def render_internship_page(meta: InternshipMeta, about: str, desc: list[str], req: list[str], benefits: list[str]) -> str:
    return f"""<!doctype html>
<html lang="vi">

  <head>
    <meta charset="utf-8">
    <meta http-equiv="x-ua-compatible" content="ie=edge">
    <meta name="description" content="">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>VNPT - Tuyển dụng - Chi tiết</title>
    <link rel="shortcut icon" href="assets/images/favicon.png" type="image/png">
    <link rel="stylesheet" href="assets/css/bootstrap.min.css">
    <link rel="stylesheet" href="assets/css/fontawesome.min.css">
    <link rel="stylesheet" href="assets/css/LineIcons.css">
    <link rel="stylesheet" href="assets/css/magnific-popup.css">
    <link rel="stylesheet" href="assets/css/default.css">
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/detail.css">
  </head>

  <body>
    <header class="header-area header-sub">
      <div class="navgition navgition-transparent">
        <div class="container">
          <div class="row">
            <div class="col-lg-12">
              <nav class="navbar navbar-expand-lg">
                <a class="navbar-brand" href="index.html">VNPT FINTECH - TUYỂN DỤNG</a>
                <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarOne" aria-controls="#navbarOne" aria-expanded="false" aria-label="Toggle navigation">
                  <span class="toggler-icon"></span>
                  <span class="toggler-icon"></span>
                  <span class="toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse sub-menu-bar" id="navbarOne">
                  <ul class="navbar-nav ml-auto">
                    <li class="nav-item"><a class="page-scroll" href="index.html">Trang chủ</a></li>
                    <li class="nav-item"><a class="page-scroll" href="index.html#about">Về chúng tôi</a></li>
                    <li class="nav-item"><a class="page-scroll" href="index.html#creation">Sáng tạo</a></li>
                    <li class="nav-item"><a class="page-scroll" href="index.html#forte">Nghề nghiệp</a></li>
                    <li class="nav-item"><a class="page-scroll" href="index.html#contact">Gia nhập</a></li>
                  </ul>
                </div>
              </nav>
            </div>
          </div>
        </div>
      </div>

      <div id="home" class="header-hero bg_cover pt-1" style="background-image: url(assets/images/banner-detail.jpg)">
        <div class="container">
          <div class="header-content">
            <h3 class="header-title">{html.escape(meta.title_short)}</h3>
          </div>
        </div>
      </div>
    </header>

    <section class="section-detail">
      <div class="container">
        <div class="job">
          <div class="row">
            <div class="col-md-4">
              <div class="job-left">
                <div class="job-item">
                  <div class="job-header">
                    <h4 class="job-title">Chi tiết</h4>
                  </div>
                  <div class="job-content">
                    <div class="metadata metadata-list">
                      <div class="metadata-list_section metadata-list_section--blue">
                        <h4 class="metadata-list_header">Nơi Làm Việc</h4>
                        <ul class="metadata-list_items"><li>Hà Nội</li></ul>
                      </div>
                      <div class="metadata-list_section metadata-list_section--orange">
                        <h4 class="metadata-list_header">Cấp Bậc</h4>
                        <ul class="metadata-list_items"><li>Thực tập sinh</li></ul>
                      </div>
                      <div class="metadata-list_section metadata-list_section--orange">
                        <h4 class="metadata-list_header">Hình Thức</h4>
                        <ul class="metadata-list_items"><li>Thực tập sinh/ Học việc</li></ul>
                      </div>
                      <div class="metadata-list_section metadata-list_section--orange">
                        <h4 class="metadata-list_header">Phòng Ban</h4>
                        <ul class="metadata-list_items"><li>{html.escape(meta.department)}</li></ul>
                      </div>
                      <div class="metadata-list_section metadata-list_section--orange">
                        <h4 class="metadata-list_header">Hạn Ứng Tuyển</h4>
                        <ul class="metadata-list_items"><li>Đang mở</li></ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="col-md-8">
              <div class="job-right">
                <div class="job-item">
                  <div class="job-header">
                    <h2 class="title">Giới Thiệu</h2>
                  </div>
                  <div class="job-content">
                    <ul class="desc-list">
                      <li>{html.escape(about)}</li>
                    </ul>
                  </div>
                </div>
                <div class="job-item">
                  <div class="job-header">
                    <h2 class="title">Mô Tả Công Việc</h2>
                  </div>
                  <div class="job-content">
                    <ul class="desc-list">
{render_list(desc)}
                    </ul>
                  </div>
                </div>
                <div class="job-item">
                  <div class="job-header">
                    <h2 class="title">Yêu Cầu Ứng Viên</h2>
                  </div>
                  <div class="job-content">
                    <ul class="desc-list">
{render_list(req)}
                    </ul>
                  </div>
                </div>
                <div class="job-item">
                  <div class="job-header">
                    <h2 class="title">Quyền Lợi</h2>
                  </div>
                  <div class="job-content">
                    <ul class="desc-list">
{render_list(benefits)}
                    </ul>
                  </div>
                  <a href="recruitment.html" class="recuitment-link">Ứng tuyển ngay <i class="lni-arrow-right"></i></a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <footer id="footer" class="footer-area">
      <div class="footer-copyright">
        <div class="container">
          <div class="row">
            <div class="col-lg-12">
              <div class="copyright text-center">
                <p class="text">Sản phẩm được thực hiện bởi team Nhân Sự của VNPT FinTech</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>

    <a class="back-to-top" href="#"><i class="lni-chevron-up"></i></a>

    <script src="assets/js/vendor/modernizr-3.6.0.min.js"></script>
    <script src="assets/js/vendor/jquery-1.12.4.min.js"></script>
    <script src="assets/js/bootstrap.min.js"></script>
    <script src="assets/js/popper.min.js"></script>
    <script src="assets/js/jquery.easing.min.js"></script>
    <script src="assets/js/scrolling-nav.js"></script>
    <script src="assets/js/jquery.magnific-popup.min.js"></script>
    <script src="assets/js/main.js"></script>
  </body>

</html>
"""


def refresh_internship_pages() -> None:
    for meta in INTERNSHIP_FILES:
        docx_path = INTERNSHIP_DIR / meta.source_name
        about, desc, req, benefits = split_docx_sections(docx_path)
        page = render_internship_page(meta, about, desc, req, benefits)
        (ROOT / meta.slug).write_text(page, encoding="utf-8")


def strip_beacon_from_existing_pages() -> None:
    for html_path in ROOT.glob("*.html"):
        html_text = html_path.read_text(encoding="utf-8")
        cleaned = strip_cloudflare_beacon(html_text)
        if cleaned != html_text:
            html_path.write_text(cleaned, encoding="utf-8")


def main() -> None:
    transcode_video()
    refresh_index()
    refresh_internship_pages()
    strip_beacon_from_existing_pages()
    print("refresh_t426: ok")


if __name__ == "__main__":
    main()
