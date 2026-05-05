# VNPT FinTech Recruitment Clone

## Setup (Linux)
```bash
python3 -m pip install -r requirements.txt
npm install
```

## Run locally
```bash
npm run start
```

Mặc định site chạy tại `http://127.0.0.1:4173/`.

## Run checks
```bash
npm run test:content
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/path/to/chromium npm run test:runtime
```

Ghi chú:
- Runtime browser test cần đường dẫn tới trình duyệt Chromium/Chrome/Edge nếu máy không có ở vị trí mặc định.
- Site local đã loại bỏ Cloudflare Insights beacon để tránh request 404 và giảm nhiễu khi chạy offline/local.
- Trang runtime chỉ dùng file MP4 tối ưu cho trình duyệt. File MOV chỉ còn là nguồn đầu vào tuỳ chọn cho bước regenerate nếu bạn giữ lại nó.

## Để triển khai trên cloudflare cần bổ sung các file
```bash
.assetsignore
wrangler.toml
```
trong file wrangler.toml
```bash
name = "<tên project trên cloundflare>"
directory = "."    # file index.html ở ngay gốc repo nên để ".", nếu ở thư mục con khác thì sửa "./<sub_repo>"
```
