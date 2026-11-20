# ESG Studio

**made by Quýt** · Phiên bản 1.1.0 · Ứng dụng desktop Windows 64-bit

ESG Studio hỗ trợ đọc báo cáo PDF của doanh nghiệp, thống kê các từ khóa về công bố ESG/ESRS E5, khám phá chủ đề bằng LDA và xuất kết quả Excel. Người dùng chọn PDF và nhập thông tin ngay trên giao diện, không cần sửa mã nguồn hoặc gõ lệnh mỗi lần phân tích.

## App làm được gì?

- Phân tích một hoặc nhiều PDF có chữ hoặc trang scan.
- Nhận dạng chữ bằng OCR tiếng Việt/Anh khi cần.
- Tự lấy số trang PDF, cho phép giới hạn khoảng trang của từng file.
- Đếm từ khóa SYMB, SUBST và E5; mặc định tính cả nội dung bảng.
- Xuất số lần xuất hiện theo từng trang để kiểm tra lại với PDF.
- Chạy LDA khi đủ dữ liệu để gợi ý các chủ đề thường xuất hiện.
- Xuất workbook Excel gồm các sheet Tổng hợp, Chỉ số, Từ khóa, Chủ đề LDA và Từ khóa theo trang.
- Tự lưu danh sách PDF, thông tin nhập dở, khoảng trang, cài đặt và kết quả gần nhất.
- Co giãn giao diện và hỗ trợ cuộn chuột khi cửa sổ nhỏ.

## App chạy như thế nào?

```text
Chọn PDF và khoảng trang
         ↓
Trích chữ trực tiếp / OCR trang ít chữ
         ↓
Giữ hoặc loại chữ trong bảng theo cài đặt
         ↓
Chuẩn hóa văn bản và xác định ngôn ngữ
         ↓
Đếm từ khóa theo từng trang và tính các chỉ số
         ↓
Khám phá chủ đề bằng LDA nếu đủ dữ liệu
         ↓
Xuất Excel, CSV, JSON và báo cáo kiểm tra
```

### 1. Đọc PDF và OCR

App dùng `pdfplumber` để lấy lớp chữ có sẵn trong PDF. Trang có ít hơn 30 từ trích được sẽ được chuyển thành ảnh bằng PDFium và nhận dạng bằng Tesseract với hai bộ ngôn ngữ Việt/Anh. Bản Windows đóng gói có sẵn bộ đọc PDF và OCR, không cần cài Python hoặc Poppler riêng.

### 2. Chọn phạm vi và làm sạch

Trong giao diện, mỗi PDF mặc định được chọn từ trang 1 đến trang cuối. Người dùng có thể thu hẹp khoảng trang. Loại báo cáo PTBV/ESG/BCTN dùng để phân loại tài liệu; nó không tự chọn riêng một chương khi đã khai báo khoảng trang.

Mặc định, app giữ cả chữ trong bảng. Có thể tắt **Đếm cả nội dung trong bảng** để lọc các bảng có đường kẻ. App chuẩn hóa Unicode, chuyển chữ về chữ thường, nối từ bị ngắt dòng bằng gạch nối, bỏ URL/email, chữ số và dấu câu.

### 3. Đếm theo từ điển

Bộ mặc định có 25 mục SYMB, 14 SUBST và 27 E5, kèm các biến thể hoặc cụm từ tương ứng tiếng Việt. Người dùng có thể sao chép thành nhiều bộ cá nhân, thêm/sửa/xóa/tạm tắt mục, nhập/xuất Excel và thử đếm đoạn văn trong Cài đặt. Mỗi lần chạy lưu bản chụp từ điển và ghi tên/mã SHA-256 vào sheet Chỉ số để tái kiểm tra. App nhận diện ngôn ngữ bằng tỷ lệ ký tự có dấu tiếng Việt; kết quả này quyết định bộ mẫu từ khóa được dùng.

App khớp nguyên từ, ưu tiên cụm dài và tránh đếm chồng cùng một đoạn chữ. Ví dụ, `pre-assessment` được tính cho mục Pre-assessment, không cộng thêm cho Assessment. Mục Assessment có thể gộp `assessment` và `assessments`. Các trang được đếm độc lập để tránh ghép nhầm cụm từ qua ranh giới trang.

### 4. Tính chỉ số

| Trường | Ý nghĩa |
|---|---|
| `so_tu` | Tổng số từ sau xử lý trong phạm vi đã chọn; với tiếng Việt hiện tính theo âm tiết. |
| `so_lan` | Số lần một mục từ khóa được tính theo từ điển. |
| `tren_1000` | `so_lan / so_tu × 1.000`, dùng để so sánh báo cáo dài ngắn khác nhau. |
| `SYMB_1000` | Tổng số lần từ khóa SYMB trên 1.000 từ/âm tiết. |
| `SUBST_1000` | Tổng số lần từ khóa SUBST trên 1.000 từ/âm tiết. |
| `E5_1000` | Tổng số lần từ khóa E5 trên 1.000 từ/âm tiết. |
| `SUBST_RATIO` | `SUBST / (SUBST + SYMB)`; để trống nếu mẫu số bằng 0. |
| `pham_vi_van_ban` | Ghi rõ lần chạy có tính nội dung bảng hay không. |

Ví dụ: báo cáo có 10.000 từ sau xử lý, một từ khóa xuất hiện 20 lần thì `tren_1000 = 2`. Đây là tần suất chuẩn hóa, không phải phần trăm.

### 5. LDA

App dùng scikit-learn để phân tích chủ đề riêng cho hai nhóm ngôn ngữ. Mỗi trang đủ ít nhất 40 từ/âm tiết sau làm sạch được xem là một văn bản. Nhóm có dưới 6 trang đạt điều kiện sẽ được bỏ qua. App lọc từ bằng `min_df=3`, `max_df=0.5`, thử số chủ đề từ 4 đến 12 và chọn theo điểm UMass được tính trong chương trình.

Nhãn chủ đề là gợi ý tự động để người dùng rà soát. LDA bị bỏ qua không làm mất bảng đếm từ khóa của báo cáo xử lý thành công.

## Dữ liệu được lưu ở đâu?

Bản `.exe` lưu phiên và kết quả trong thư mục **`du_lieu` cạnh file chạy**. App nhớ đường dẫn PDF gốc; không tự sao chép PDF gốc vào phiên lưu. Khi PDF bị chuyển chỗ, dùng **Chọn lại PDF** để nối lại đường dẫn.

PDF được xử lý trên máy, không gửi nội dung ra dịch vụ bên ngoài. Bộ OCR đã đi kèm bản phát hành; chỉ cần Internet nếu phải tải bổ sung hoặc sửa bộ OCR bằng chức năng chuẩn bị tự động.

## Giới hạn cần hiểu

- OCR và trích chữ có thể sai với ảnh mờ, chữ nhỏ hoặc bố cục nhiều cột.
- Số đếm có thể khác Ctrl+F do phạm vi trang, tùy chọn bảng, khớp nguyên từ, biến thể và quy tắc ưu tiên cụm dài.
- Chế độ loại bảng không đảm bảo loại chính xác mọi bảng, đặc biệt trên trang OCR.
- Báo cáo song ngữ hiện được xếp vào một ngôn ngữ; cần kiểm tra việc nhận diện và từ khóa bị bỏ sót.
- SYMB/SUBST/E5 là nhóm từ khóa. Tần suất hoặc nhãn LDA chưa đủ để tự kết luận doanh nghiệp công bố hình thức hay thực chất.
- Từ điển và cách triển khai tài liệu phương pháp chưa được xác minh độc lập đầy đủ. Khi dùng cho nghiên cứu, cần thống nhất quy tắc và đối chiếu một mẫu bằng tay.

Hướng dẫn thao tác: [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md).
