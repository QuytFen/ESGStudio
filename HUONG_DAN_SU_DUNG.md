# Hướng dẫn sử dụng ESG Studio

**made by Quýt** · Phiên bản 1.1.1

## 1. Mở app

### Bản một file `.exe`

1. Đặt `ESGStudio-Windows-x64.exe` trong thư mục bạn có quyền ghi, chẳng hạn thư mục riêng trong Downloads hoặc Desktop.
2. Nhấp đúp để chạy. Chờ app giải nén thư viện khi khởi động.
3. Không cần cài Python, Poppler hoặc Tesseract riêng.

### Bản portable ZIP

1. Giải nén toàn bộ `ESGStudio-Windows-x64-portable.zip`.
2. Vào thư mục `ESGStudio`, nhấp đúp `ESGStudio.exe`.
3. Giữ nguyên thư mục `_internal` bên cạnh `.exe`.

Nếu dùng mã nguồn, mở bằng `Mo_app.cmd`; chạy `Cai_dat_app.cmd` một lần trước nếu chưa cài môi trường.

## 2. Thêm PDF

Vào tab **Chuẩn bị báo cáo** hoặc **Báo cáo**, bấm **+ Thêm PDF** và chọn một hay nhiều file. Tên file có thể bất kỳ. App tự đọc tổng số trang, chọn sẵn từ trang 1 đến trang cuối.

Chọn từng dòng trong danh sách để xem và sửa thông tin của PDF đó.

## 3. Điền thông tin báo cáo

| Ô nhập | Nội dung | Ví dụ |
|---|---|---|
| Mã công ty | Chữ cái không dấu và số, viết liền | `AAA` |
| Năm báo cáo | Năm 4 chữ số | `2024` |
| Tên công ty | Tên doanh nghiệp | `Công ty mẫu` |
| Ngành | Ngành hoạt động | `Nhựa và cao su` |
| Loại báo cáo | Chọn BCTN, PTBV hoặc ESG | `BCTN` |
| Kỳ báo cáo | Thời gian tài liệu đề cập | `01/01/2024–31/12/2024` |

Các loại tài liệu:

- **BCTN**: báo cáo thường niên, thường có tên *Annual Report*.
- **PTBV**: báo cáo phát triển bền vững, thường có tên *Sustainability Report*.
- **ESG**: báo cáo môi trường, xã hội và quản trị, thường có tên *ESG Report*.

**Chọn PTBV không có nghĩa là app tự chọn phần 5 của PDF.** Muốn phân tích một chương cụ thể, chọn khoảng trang chứa chương đó. Các báo cáo cùng mã công ty/năm cần thống nhất tên công ty, ngành và kỳ báo cáo; khoảng trang của từng file được giữ riêng.

## 4. Chọn trang

- **Từ trang**: chọn từ 1 đến trang cuối PDF.
- **Đến trang**: chỉ cho chọn từ trang bắt đầu đến trang cuối PDF.
- Đổi trang bắt đầu vượt trang kết thúc đang chọn sẽ làm app tự nâng trang kết thúc lên cho hợp lệ.
- Trang được tính theo thứ tự trong PDF, bắt đầu từ 1, không theo số in ở chân trang.

Ví dụ: PDF có 123 trang; chọn Từ trang = 40 thì Đến trang chỉ cho chọn 40–123. Muốn chỉ đọc trang PDF số 5, đặt cả hai ô bằng 5.

## 5. Chọn cách đếm và nơi lưu

Mở tab **Cài đặt & hướng dẫn** hoặc **Cài đặt**:

- **Đếm cả nội dung trong bảng** mặc định được bật. Giữ bật nếu muốn tính cả chữ trong bảng của các trang đã chọn.
- Nếu phương pháp nghiên cứu yêu cầu loại bảng, bỏ chọn mục này. App sẽ lọc các bảng có đường kẻ; trang OCR vẫn cần rà soát thủ công.
- **Nơi lưu kết quả** cho phép chọn thư mục đầu ra. Mỗi lần chạy tạo một thư mục riêng để giữ lại kết quả cũ.
- **Chuẩn bị OCR tự động** dùng khi bộ OCR chưa sẵn sàng hoặc cần tải bổ sung. Bản `.exe` phát hành đã kèm OCR tiếng Việt/Anh.

`so_lan`, `so_tu` và các tần suất được tính trên cùng phạm vi trang và tùy chọn bảng.

## 6. Phân tích

1. Kiểm tra thông tin của tất cả PDF.
2. Bấm **Bắt đầu phân tích**.
3. Theo dõi tab **Kết quả phân tích** hoặc **Kết quả** và vùng **Nhật ký xử lý**.
4. Chờ xử lý hoàn tất trước khi đóng app.

Một PDF bị lỗi không ngăn các PDF khác tiếp tục xử lý. Nhật ký ghi file bị lỗi và nguyên nhân.

## 7. Mở và đọc Excel

Bấm **Mở file Excel** sau khi phân tích. Nếu máy có Microsoft Excel, app ưu tiên mở trực tiếp bằng Excel. Khi chưa chạy trong phiên hiện tại, nút này cũng cho phép chọn file `.xlsx` đã lưu.

| Sheet | Nội dung |
|---|---|
| Tổng hợp | Bảng 21 cột để tổng hợp thông tin nghiên cứu; một dòng mỗi doanh nghiệp theo quy tắc chọn báo cáo. |
| Chỉ số | Một dòng mỗi báo cáo: khoảng trang, tổng từ, tần suất các nhóm, tỷ lệ SUBST và phạm vi văn bản. |
| Từ khóa | Một dòng mỗi từ khóa/báo cáo: số lần xuất hiện và tần suất trên 1.000 từ/âm tiết. |
| Chủ đề LDA | Các chủ đề, từ khóa, nhãn gợi ý và tỷ trọng nếu đủ dữ liệu. |
| Từ khóa theo trang | Số lần từ khóa xuất hiện ở từng trang PDF; chỉ ghi các mục có xuất hiện. |

Ba cột dễ nhầm:

- **`so_tu`**: tổng số từ sau xử lý; tiếng Việt hiện tính theo âm tiết.
- **`so_lan`**: số lần một từ khóa/cụm từ khóa được tính.
- **`tren_1000`**: `so_lan / so_tu × 1.000`. Ví dụ 20 lần trong 10.000 từ thì bằng 2, không phải 2%.

Để đối chiếu một từ khóa, lọc mã công ty, năm, loại báo cáo, nhóm và từ khóa trong sheet **Từ khóa theo trang**. Cộng `so_lan` của các trang sẽ bằng số đếm tổng trong sheet **Từ khóa**.

## 8. Tự lưu và mở lại

App tự lưu sau một khoảng dừng nhập ngắn và khi đóng. Mở lại sẽ khôi phục PDF, thông tin nhập dở, khoảng trang, cài đặt và kết quả gần nhất.

Bản `.exe` dùng cấu trúc:

```text
ESGStudio-Windows-x64.exe
du_lieu/
  .app_state/session.json
  ket_qua/
    thư_mục_mỗi_lần_chạy/
```

Nếu đã chọn nơi xuất khác, kết quả nằm ở thư mục bạn chọn. App nhớ đường dẫn PDF gốc, vì vậy hãy giữ PDF ở vị trí cũ hoặc dùng **Chọn lại PDF** khi đã chuyển file. Thao tác chọn lại vẫn giữ thông tin công ty đã nhập.

## 9. Cửa sổ nhỏ và con lăn

- Thu nhỏ cửa sổ sẽ làm danh sách, biểu mẫu và các nút tự xếp lại.
- Đặt chuột trên vùng muốn cuộn rồi lăn: tab, bảng hoặc nhật ký.
- Giữ **Shift + lăn chuột** để cuộn ngang bảng; cũng có thể kéo thanh cuộn ngang.
- Có thể dùng phím Tab để di chuyển giữa các ô nhập.

## 10. Các tình huống thường gặp

### Ctrl+F có số khác `so_lan`

Kiểm tra đúng PDF, khoảng trang và tùy chọn bảng. App khớp nguyên từ, có gộp biến thể và ưu tiên cụm dài, nên cách đếm có thể khác tìm chuỗi con. Ví dụ Assessment gộp `assessment/assessments`; `pre-assessment` được tính riêng. OCR có thể sai hoặc thiếu chữ. Dùng sheet theo trang để xác định chỗ lệch.

### Đổi cài đặt nhưng Excel vẫn như cũ

File kết quả cũ không tự tính lại. Bấm **Bắt đầu phân tích** để tạo kết quả mới, rồi mở Excel của lần chạy mới. Cột `pham_vi_van_ban` trong sheet Chỉ số cho biết có tính bảng hay không.

### LDA vi báo “Bỏ qua”, LDA en báo “OK”

Nhóm tiếng Việt chưa đủ dữ liệu để chạy LDA, còn nhóm tiếng Anh đã chạy được. Bảng đếm từ khóa vẫn được xuất cho các báo cáo xử lý thành công. Nếu tài liệu là tiếng Việt nhưng bị xếp vào tiếng Anh, cần rà soát nhận diện ngôn ngữ.

### File Excel không ghi đè/mở được

Kiểm tra file còn tồn tại, nơi lưu có quyền ghi và máy có ứng dụng đọc `.xlsx`. Nếu file đang bị Excel giữ, đóng file đó rồi thử lại. Khi mở kết quả mới có cùng tên với workbook khác đang mở, đóng workbook cũ trước.

### PDF cần chọn lại

Chọn dòng có đánh dấu **Chọn lại PDF**, bấm nút cùng tên rồi chọn đúng file. App sẽ đọc lại số trang và giữ thông tin công ty.

### Muốn cập nhật app

Đóng app trước khi thay file `.exe`. Giữ thư mục `du_lieu` và các PDF gốc để giữ phiên làm việc. Với bản portable, cập nhật cả các thư viện đi kèm, không trộn `_internal` của các phiên bản.

Thông tin về cơ chế xử lý và giới hạn: [GIOI_THIEU_APP.md](GIOI_THIEU_APP.md).

## Tùy chỉnh bộ từ điển (từ phiên bản 1.1.0)

Trong **Cài đặt & hướng dẫn**, chọn bộ từ điển cho lần chạy tiếp theo. Bấm **Sao chép thành bộ riêng** để giữ bộ mặc định và tạo bản cá nhân.

- Mỗi mục gồm nhóm SYMB/SUBST/E5, tên, biến thể Anh/Việt và trạng thái **Dùng**. Mỗi biến thể nằm trên một dòng.
- Chọn mục để sửa, bấm **Áp dụng mục** trước khi chọn mục khác, rồi **Lưu bộ từ điển**. Có thể thêm, xóa và tạm tắt mục. Giữ mẫu regex tiếng Anh có sẵn nếu chưa cần sửa quy tắc nâng cao.
- Bốn nút thao tác luôn cố định ở góc phải dưới, tự xuống hàng khi cửa sổ hẹp. Thông báo sau thao tác cho biết mục đã áp dụng/xóa trong bản đang chỉnh hay bộ từ điển đã được lưu xuống máy.
- Ô **Thử đếm** kiểm tra các mục đã áp dụng theo ngôn ngữ vi/en được chọn.
- **Xuất Excel / mẫu** để chỉnh hàng loạt. File mở đầu bằng sheet **Hướng dẫn** với cách điền từng cột và dòng mẫu; chuyển sang sheet **Từ điển** để chỉnh dữ liệu. Trong ô dùng Alt+Enter để xuống dòng. Giữ nguyên tiêu đề, cột `bat` là 1 hoặc 0. Ví dụ trong hướng dẫn không tự được nhập. **Nhập Excel** tạo bộ mới.
- Mỗi lần chạy lưu `tu_dien_da_dung.json`; sheet Chỉ số ghi tên và mã SHA-256 của bộ đã dùng. Muốn áp dụng sửa đổi cần chạy lại phân tích.
- Bộ cá nhân nằm trong `tu_dien_ca_nhan` của thư mục dữ liệu; bản exe là `du_lieu/tu_dien_ca_nhan`. Giữ cả thư mục dữ liệu khi cập nhật app.
