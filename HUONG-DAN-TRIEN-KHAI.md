# Hướng dẫn triển khai chi tiết

Tài liệu này hướng dẫn từng thao tác, dành cho người chưa quen GitHub. Tổng thời gian khoảng 15–20 phút.
Làm đúng thứ tự, vì bước sau phụ thuộc bước trước.

---

## Trước khi bắt đầu: hai quyết định

### Quyết định 1 — Repo để Private hay Public?

GitHub Pages **không xuất bản trang từ repo Private ở gói Free**. Tài liệu GitHub ghi: Pages có ở repo
public với gói Free, và ở cả public lẫn private với gói **Pro, Team, Enterprise**.

| Chọn | Hệ quả |
|---|---|
| **Public** | Miễn phí, chạy ngay. Nhưng toàn bộ sổ tra 401 chất và phần diễn giải căn cứ pháp lý sẽ công khai trên mạng. |
| **Private + gói Pro** (~4 USD/tháng, tài khoản cá nhân) | Giữ kín, mở được ngay trong hôm nay. |
| **Private + tổ chức công ty, gói Team** | Đúng chuẩn doanh nghiệp: repo thuộc công ty, phân quyền theo phòng ban, người nghỉ việc không mang đi được. |

Nếu đây là công cụ nội bộ cho nhà máy và khách hàng, chọn hướng thứ hai hoặc thứ ba.
Muốn chạy thử trước cho biết thì cứ để Public, sau đổi lại được.

### Quyết định 2 — Đẩy mã lên bằng cách nào?

| Cách | Phù hợp với |
|---|---|
| **GitHub Desktop** | Không cần gõ lệnh. Khuyến nghị nếu bạn không phải dân lập trình. |
| **Dòng lệnh (git)** | Nhanh hơn nếu đã quen terminal. Cần tạo Personal Access Token. |
| Kéo thả trên web | **Không khuyến nghị** — thư mục `.github` bắt đầu bằng dấu chấm nên hệ điều hành ẩn đi, rất dễ upload thiếu, mà thiếu nó thì không có gì chạy tự động. |

---

## Bước 1 — Tạo kho mã (repository)

Vào <https://github.com/new>.

Điền đúng như sau:

| Ô | Điền gì | Lý do |
|---|---|---|
| **Owner** | `Viet0302`, hoặc chọn tổ chức công ty trong danh sách xổ xuống | Repo thuộc tổ chức thì không phụ thuộc một cá nhân |
| **Repository name** | `phu-gia-regwatch` | Chữ thường, không dấu, nối bằng gạch ngang. Tên này nằm trong địa chỉ trang và **phân biệt hoa thường** |
| **Description** | `Theo dõi văn bản pháp luật về phụ gia thực phẩm — Codex và 8 thị trường` | Tùy ý, có dấu được |
| **Visibility** | Theo quyết định 1 ở trên | |
| **Add README** | **OFF** ← quan trọng | Bật lên là repo đã có sẵn một commit, lúc đẩy mã lên sẽ bị từ chối. Gói mã đã có sẵn README rồi |
| **Add .gitignore** | No | Gói mã đã có |
| **Add license** | No | Nội bộ, không cần |

Bấm **Create repository**.

Màn hình tiếp theo hiện một trang trống kèm địa chỉ dạng
`https://github.com/Viet0302/phu-gia-regwatch.git` — **để nguyên tab này**, lát nữa dùng đến.

> **Nếu bạn lỡ bật "Add README"**: không sao. Làm theo cách GitHub Desktop ở bước 2 (clone về rồi copy
> đè), hoặc nếu dùng dòng lệnh thì thêm `git pull --rebase origin main` trước khi `git push`.

---

## Bước 2 — Đẩy mã nguồn lên

Giải nén `phu-gia-regwatch.zip`. Bên trong có một thư mục tên `phu-gia-regwatch`, chứa:

```
phu-gia-regwatch/
├── .github/workflows/daily.yml   ← file chạy tự động (quan trọng nhất)
├── data/                         ← nơi lưu trạng thái, ban đầu rỗng
├── scripts/                      ← hai kịch bản Python
├── site/                         ← giao diện + sổ tra phụ gia
├── watchlist.yml                 ← danh sách 20 nguồn theo dõi
├── requirements.txt
├── README.md
└── HUONG-DAN-TRIEN-KHAI.md       ← file bạn đang đọc
```

### Cách A — GitHub Desktop (khuyến nghị)

1. Tải và cài **GitHub Desktop**: <https://desktop.github.com>
2. Mở lên, bấm **Sign in to GitHub.com**, đăng nhập tài khoản `Viet0302`.
3. Menu **File → Clone repository** → tab **GitHub.com** → chọn `phu-gia-regwatch` → chọn thư mục lưu
   trên máy → bấm **Clone**.
   Máy sẽ tạo một thư mục trống, ví dụ `C:\Users\Viet\Documents\GitHub\phu-gia-regwatch`.
4. Mở thư mục đó. Mở song song thư mục vừa giải nén.
5. **Copy toàn bộ thứ bên trong** thư mục giải nén (`.github`, `data`, `scripts`, `site`,
   `watchlist.yml`, `requirements.txt`, `README.md`, `HUONG-DAN-TRIEN-KHAI.md`) **sang** thư mục vừa clone.

   > Copy phần **bên trong**, không copy cả thư mục cha. Sau khi copy, trong thư mục clone phải nhìn thấy
   > ngay `watchlist.yml`, chứ không phải một thư mục `phu-gia-regwatch` lồng bên trong.

   > **Windows**: thư mục `.github` có thể bị ẩn. Vào File Explorer → tab **View** → tick **Hidden items**.
   > **macOS**: bấm `Cmd + Shift + .` để hiện file ẩn.

6. Quay lại GitHub Desktop. Cột trái giờ liệt kê một loạt file mới. **Kiểm tra trong danh sách có
   `.github/workflows/daily.yml`** — nếu không có là bạn copy thiếu, quay lại bước 5.
7. Ô **Summary** dưới cùng bên trái, gõ: `Khởi tạo trang theo dõi văn bản phụ gia`
8. Bấm **Commit to main**, rồi bấm **Push origin** ở thanh trên.

Xong. Mở lại tab GitHub trên trình duyệt, F5, sẽ thấy đủ file.

### Cách B — Dòng lệnh

Cần cài Git trước (<https://git-scm.com/downloads>).

```bash
cd đường/dẫn/tới/phu-gia-regwatch
git init
git branch -M main
git remote add origin https://github.com/Viet0302/phu-gia-regwatch.git
git add .
git commit -m "Khởi tạo trang theo dõi văn bản phụ gia"
git push -u origin main
```

Khi hiện hộp thoại hỏi đăng nhập:

- **Username**: `Viet0302`
- **Password**: **không phải mật khẩu GitHub** mà là *Personal Access Token*.

Tạo token: GitHub → bấm ảnh đại diện góc phải → **Settings** → cuộn xuống cuối cột trái, **Developer
settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**.
Đặt tên bất kỳ, chọn thời hạn, **tick hai ô: `repo` và `workflow`** (thiếu `workflow` thì không đẩy được
file chạy tự động lên). Bấm **Generate token**, copy chuỗi ký tự hiện ra — nó chỉ hiện một lần — rồi dán
vào ô Password.

---

## Bước 3 — Bật GitHub Pages

Trong repo (không phải Settings của tài khoản):

1. Bấm tab **Settings** ở thanh ngang phía trên repo.
2. Cột trái, mục **Code and automation**, bấm **Pages**.
3. Phần **Build and deployment** → ô **Source** đang là `Deploy from a branch` → đổi thành
   **`GitHub Actions`**.

Không có nút Save, đổi xong là tự lưu. Không cần chọn nhánh hay thư mục.

> Nếu mục **Pages** không xuất hiện trong cột trái, hoặc hiện dòng chữ yêu cầu nâng cấp: repo đang Private
> mà tài khoản ở gói Free. Quay lại quyết định 1.

---

## Bước 4 — Mở quyền ghi cho workflow

Vẫn trong **Settings** của repo:

1. Cột trái, cuộn xuống mục **Code and automation**, bấm **Actions** → **General**.
2. Cuộn xuống gần cuối trang, tới mục **Workflow permissions**.
3. Chọn **Read and write permissions**.
4. Bấm **Save** ngay dưới đó.

Bước này cho phép workflow tự ghi lại trạng thái theo dõi (`data/state.json`, `data/changelog.json`) vào
repo và mở issue báo tin. Bỏ qua bước này thì workflow chạy đến bước lưu kết quả sẽ báo lỗi `403`.

---

## Bước 5 — Chạy thử lần đầu

1. Bấm tab **Actions** ở thanh ngang phía trên repo.
2. Lần đầu vào, GitHub có thể hỏi xác nhận bật Actions — bấm nút xanh **I understand my workflows, go
   ahead and enable them**.
3. Cột trái hiện tên workflow: **Theo dõi văn bản phụ gia**. Bấm vào.
4. Bên phải hiện dòng chữ *This workflow has a workflow_dispatch event trigger* kèm nút **Run workflow**.
   Bấm nút đó → giữ nhánh `main` → bấm nút xanh **Run workflow**.
5. Đợi vài giây rồi F5. Sẽ thấy một dòng chạy với vòng tròn vàng. Bấm vào để xem tiến trình.

Lần chạy đầu mất khoảng **2–4 phút** (phải cài thư viện Python và tải 18 nguồn).

### Kết quả mong đợi

Hai ô việc **check** và **deploy** đều có dấu tick xanh. Bấm vào `deploy` sẽ thấy địa chỉ trang:

```
https://viet0302.github.io/phu-gia-regwatch/
```

Cũng xem được ở **Settings → Pages**, dòng *Your site is live at…*.

Mở địa chỉ đó sẽ thấy:

- hàng số liệu: 20 nguồn, bao nhiêu nguồn bình thường, bao nhiêu cần kiểm tra thủ công
- bảng 20 nguồn theo thị trường, kèm trạng thái và ngày kiểm tra
- nhật ký ghi 20 dòng *"bắt đầu theo dõi"* — đây là mốc khởi tạo, **không phải** luật vừa thay đổi
- link sang `tra-cuu.html` — sổ tra 401 chất

Lần chạy đầu **không mở issue**, đúng như thiết kế: chỉ khi có thay đổi nội dung thật mới báo tin.

Từ hôm sau, workflow tự chạy lúc **08:00 giờ Việt Nam** mỗi ngày.

> GitHub đôi khi chạy trễ vài chục phút so với giờ hẹn khi hệ thống bận. Bình thường, không phải lỗi.

---

## Lỗi thường gặp

| Thông báo | Nguyên nhân | Xử lý |
|---|---|---|
| `! [rejected] main -> main (fetch first)` | Repo đã có commit sẵn (lỡ bật Add README) | `git pull --rebase origin main` rồi `git push` lại |
| `Support for password authentication was removed` | Nhập mật khẩu GitHub thay vì token | Tạo Personal Access Token, xem bước 2 cách B |
| `refusing to allow ... without 'workflow' scope` | Token thiếu quyền `workflow` | Tạo token mới, tick thêm ô `workflow` |
| `remote: Permission to ... denied to github-actions[bot]` hoặc `403` ở bước *Lưu kết quả vào kho mã* | Chưa làm bước 4 | Làm bước 4, rồi chạy lại workflow |
| `Get Pages site failed` / `Failed to create deployment (404)` | Chưa làm bước 3, hoặc repo Private ở gói Free | Làm bước 3; nếu Private thì xem quyết định 1 |
| Trang báo 404 dù deploy xanh | Địa chỉ gõ sai hoa/thường, hoặc chưa kịp lan truyền | Copy đúng địa chỉ ở Settings → Pages, đợi 1–2 phút |
| Vài nguồn hiện *"Không truy cập được"* | Trang nguồn chặn, đổi địa chỉ, hoặc tạm ngưng | Bình thường. Mở địa chỉ trong `watchlist.yml` kiểm tra; nếu trang đổi link thì sửa lại trong file đó |
| Nhật ký báo thay đổi nhưng đọc trích đoạn thấy toàn chữ lặt vặt | Trang nguồn đổi giao diện, không phải đổi luật | Đọc trích đoạn rồi bỏ qua. Đây là lý do máy chỉ báo, không tự sửa dữ liệu |

---

## Việc hằng ngày sau khi chạy được

1. **Có thay đổi** → GitHub gửi email (nếu bạn đã bấm **Watch → All Activity** ở góc trên repo).
2. Mở trang, đọc trích đoạn khác biệt trong nhật ký.
3. Mở văn bản gốc theo link, xác minh đúng là sửa đổi pháp lý.
4. Nếu đúng: cập nhật dữ liệu sổ tra theo quy trình duyệt của công ty, rồi thay
   `site/tra-cuu.html` và `site/pg-detail.json`, commit lại.

Trang **chỉ báo, không tự sửa dữ liệu tra cứu**. Đây là chủ ý: dữ liệu pháp lý dùng cho hồ sơ công bố
sản phẩm không nên để máy ghi đè mà không có người duyệt.

---

## Muốn nhận thông báo vào Teams hoặc Slack

Xem mục *Nhận thông báo* trong `README.md`.
