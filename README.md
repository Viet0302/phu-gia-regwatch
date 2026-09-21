# Trang theo dõi văn bản phụ gia thực phẩm

Trang web nội bộ chạy trên GitHub Pages, mỗi ngày tự kiểm tra các văn bản pháp luật về phụ gia thực phẩm
tại Codex và 8 thị trường (Việt Nam, Mỹ, Úc/NZ, Thái Lan, EU, Hồng Kông, Mông Cổ, Đài Loan), ghi lại thay
đổi và báo cho người phụ trách.

Trang gồm hai phần:

| Trang | Nội dung |
|---|---|
| `index.html` | Bảng 20 nguồn đang theo dõi, trạng thái từng nguồn, nhật ký thay đổi kèm trích đoạn |
| `tra-cuu.html` | Sổ tra phụ gia: 401 chất × Codex + 8 thị trường, căn cứ pháp lý, kiểm tra công thức |

Ngoài ra có `feed.xml` (RSS, đăng ký được trong Outlook/Teams), `changelog.json` và `status.json` cho hệ
thống khác đọc vào.

---

## Triển khai lần đầu (khoảng 10 phút)

> Chưa quen GitHub? Mở **`HUONG-DAN-TRIEN-KHAI.md`** — hướng dẫn từng thao tác click, kèm bảng lỗi
> thường gặp. Phần dưới đây là bản rút gọn cho người đã quen.

### 1. Tạo kho mã

Trên tài khoản GitHub của công ty, tạo một repository mới, ví dụ `phu-gia-regwatch`. **Tắt "Add README"**
(gói mã đã có sẵn; bật lên sẽ làm bước đẩy mã bị từ chối).

Để **Private** nếu chỉ dùng nội bộ — nhưng lưu ý GitHub Pages chỉ xuất bản từ repo private khi tài khoản
ở gói **Pro, Team hoặc Enterprise**. Gói Free thì phải để **Public**.

### 2. Đẩy mã nguồn lên

```bash
unzip phu-gia-regwatch.zip && cd phu-gia-regwatch
git init && git branch -M main
git remote add origin https://github.com/<tài-khoản>/phu-gia-regwatch.git
git add . && git commit -m "Khởi tạo trang theo dõi văn bản phụ gia"
git push -u origin main
```

### 3. Bật GitHub Pages

Trong repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Không cần chọn nhánh.

### 4. Cho phép workflow ghi vào repo

**Settings → Actions → General → Workflow permissions → Read and write permissions** → Save.

### 5. Chạy thử ngay

**Actions → Theo dõi văn bản phụ gia → Run workflow**. Lần chạy đầu sẽ:

- kiểm tra 20 nguồn, ghi `data/state.json`
- tạo nhật ký khởi tạo trong `data/changelog.json`
- dựng trang và xuất bản lên `https://<tài-khoản>.github.io/phu-gia-regwatch/`

Từ hôm sau, workflow tự chạy lúc **01:00 UTC (08:00 giờ Việt Nam)** mỗi ngày.

---

## Cách hoạt động

```
watchlist.yml ──► scripts/check_sources.py ──► data/state.json     (trạng thái từng nguồn)
                          │                    data/changelog.json (nhật ký thay đổi)
                          ▼
                  scripts/build_site.py ──► site_out/ ──► GitHub Pages
                          │
                          └─► có thay đổi thì mở một Issue trong repo
```

Với mỗi nguồn, kịch bản: đọc `robots.txt` (nguồn nào cấm thì bỏ qua và đánh dấu “kiểm tra thủ công”),
tải nội dung, bỏ các phần biến động như giờ/token, chuẩn hóa thành văn bản thuần, băm SHA-256 rồi so với
lần trước. Khác nhau thì ghi lại kèm tối đa 30 dòng khác biệt.

**Trang chỉ báo thay đổi, không tự sửa dữ liệu tra cứu.** Người phụ trách đọc nhật ký, mở văn bản gốc,
rồi cập nhật dữ liệu theo quy trình duyệt của công ty. Đây là chủ ý: dữ liệu pháp lý không nên để máy tự
ghi đè.

---

## Thêm hoặc sửa nguồn theo dõi

Mở `watchlist.yml`, thêm một mục:

```yaml
  - id: vn-thong-tu-moi          # mã duy nhất, không dấu
    market: Việt Nam             # tên thị trường, dùng để nhóm trên trang
    name: Thông tư XX/2027/TT-BYT
    url: https://...
    kind: html                   # html | pdf | json | head
    manual: false                # true nếu nguồn chặn công cụ tự động
    note: Ghi chú hiển thị dưới tên nguồn
```

`kind`:

- `html` — lấy phần nội dung chính của trang (ưu tiên thẻ `<main>`/`<article>`)
- `pdf` — tải file, rút text bằng `pdftotext`, so nội dung; không rút được text thì so nội dung file
- `json` — so nội dung JSON (dùng cho API eCFR của Mỹ)
- `head` — chỉ so `ETag`, `Last-Modified`, kích thước; dùng cho file lớn ít đổi

Commit là xong, lần chạy kế tiếp áp dụng ngay.

---

## Nhận thông báo

Mặc định mỗi lần có thay đổi, workflow mở một **Issue** trong repo. Ai theo dõi repo (Watch → All
Activity) sẽ nhận email từ GitHub.

Muốn gửi vào Teams hoặc Slack: tạo webhook của kênh, lưu vào **Settings → Secrets and variables →
Actions** với tên `CHAT_WEBHOOK`, rồi thêm bước này vào cuối job `check` trong
`.github/workflows/daily.yml`:

```yaml
      - name: Báo vào kênh chat
        if: steps.run.outputs.changed == 'true' && env.HOOK != ''
        env:
          HOOK: ${{ secrets.CHAT_WEBHOOK }}
        run: |
          curl -s -H 'Content-Type: application/json' -d "{\"text\":\"Văn bản phụ gia có ${{ steps.run.outputs.count }} thay đổi hôm nay. Xem: https://<tài-khoản>.github.io/phu-gia-regwatch/\"}" "$HOOK"
```

---

## Cập nhật dữ liệu tra cứu

Trang `tra-cuu.html` và `pg-detail.json` trong thư mục `site/` là bản dựng sẵn của sổ tra phụ gia. Khi có
bản dữ liệu mới, thay hai file đó rồi commit; workflow kế tiếp sẽ xuất bản.

---

## Chạy thử trên máy

```bash
pip install -r requirements.txt
sudo apt-get install -y poppler-utils        # để đọc PDF
python scripts/check_sources.py              # kiểm tra nguồn, ghi data/
python scripts/build_site.py                 # dựng site_out/
python -m http.server -d site_out 8000       # mở http://localhost:8000
```

`python scripts/check_sources.py --dry-run` chạy thử mà không ghi file.

---

## Giới hạn cần biết

- **Chu kỳ một ngày**, không phải thời gian thực. Muốn dày hơn thì sửa `cron` trong workflow (GitHub cho
  phép tối thiểu 5 phút, nhưng các cổng thông tin nhà nước không đổi nhanh đến vậy).
- **Một số nguồn chặn công cụ tự động**: GSFA Online của FAO, e-Legislation Hồng Kông, vfa.gov.vn. Các
  nguồn này để `manual: true`, trang sẽ nhắc kiểm tra tay thay vì báo sai.
- **Thay đổi giao diện trang nguồn cũng bị tính là thay đổi.** Đọc trích đoạn trong nhật ký để phân biệt
  sửa đổi pháp lý thật với thay đổi kỹ thuật của website.
- GitHub Actions ở gói Free có hạn mức phút chạy; tác vụ này tốn khoảng 1–2 phút mỗi ngày.
