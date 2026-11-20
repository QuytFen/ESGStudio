# ESG Studio

**made by Quýt** · Phiên bản 1.1.1 · Windows 64-bit

ESG Studio là ứng dụng desktop hỗ trợ phân tích báo cáo PDF của doanh nghiệp: trích chữ, nhận dạng trang scan, thống kê từ khóa SYMB/SUBST/E5, khám phá chủ đề bằng LDA và xuất kết quả Excel. Bạn chọn file và nhập thông tin ngay trên giao diện, không cần gõ lệnh mỗi lần sử dụng.

**[Tải app tại Releases](https://github.com/QuytFen/ESGStudio/releases)** · [Giới thiệu chi tiết](GIOI_THIEU_APP.md) · [Hướng dẫn riêng](HUONG_DAN_SU_DUNG.md)

## Tải và mở app

1. Bấm **[Releases](https://github.com/QuytFen/ESGStudio/releases)** hoặc mục **Releases** ở bên phải trang repo.
2. Chọn phiên bản muốn tải, mở mục **Assets** và chọn một trong hai gói bên dưới.
3. Tải về máy Windows 64-bit và mở theo hướng dẫn của gói đã chọn.

| Gói tải | Cách mở | Đặc điểm |
|---|---|---|
| `ESGStudio-Windows-x64.exe` | Đặt trong một thư mục có quyền ghi rồi nhấp đúp để chạy. | Một file chứa app, thư viện và OCR. Khi mở cần chờ giải nén thư viện tạm. |
| `ESGStudio-Windows-x64-portable.zip` | Bấm **Extract all / Giải nén tất cả**, vào thư mục `ESGStudio` vừa giải nén rồi chạy `ESGStudio.exe`. | Thư viện nằm riêng trong `_internal`; giữ nguyên toàn bộ thư mục để app chạy. |

Hai gói có cùng chức năng. **Không cần cài Python, Poppler hoặc Tesseract riêng** khi dùng bản app đã đóng gói.

Hãy chọn đúng file app trong **Assets**. Các mục **Source code (zip)** và **Source code (tar.gz)** là gói mã nguồn, không phải bản app chạy sẵn. Nếu chưa thấy hai file app, phiên bản đó chưa được đính kèm bộ cài/chạy; hãy kiểm tra một release khác hoặc chờ tác giả tải lên.

## Tính năng

- Đọc một hoặc nhiều PDF, hỗ trợ OCR tiếng Việt và tiếng Anh cho trang ít chữ.
- Tự xác định số trang, cho phép chọn khoảng trang riêng cho từng báo cáo.
- Đếm theo bộ từ khóa SYMB, SUBST và E5; mặc định tính cả chữ trong bảng.
- Quản lý nhiều bộ từ điển cá nhân, sửa biến thể Anh/Việt, bật/tắt từ khóa, nhập/xuất Excel và thử đếm đoạn văn.
- Xuất số đếm theo từng trang PDF để đối chiếu.
- Phân tích chủ đề bằng LDA khi đủ dữ liệu.
- Xuất Excel với các bảng tổng hợp, chỉ số, từ khóa và chủ đề.
- Tự lưu danh sách PDF, thông tin nhập dở, khoảng trang, cài đặt và kết quả gần nhất.
- Giao diện tự xếp lại khi thu nhỏ, có thanh cuộn và hỗ trợ con lăn chuột.

## Hướng dẫn sử dụng

### 1. Thêm báo cáo PDF

Vào tab **Chuẩn bị báo cáo** (hoặc **Báo cáo** khi cửa sổ nhỏ), bấm **+ Thêm PDF**. Có thể chọn nhiều file cùng lúc và tên file bất kỳ. Chọn từng dòng trong danh sách để chỉnh thông tin của file đó.

### 2. Điền thông tin

| Ô nhập | Nội dung | Ví dụ |
|---|---|---|
| Mã công ty | Chữ cái không dấu và số, viết liền. | `AAA` |
| Năm báo cáo | Năm có 4 chữ số. | `2024` |
| Tên công ty | Tên doanh nghiệp. | `Công ty mẫu` |
| Ngành | Ngành hoạt động. | `Nhựa và cao su` |
| Loại báo cáo | Chọn BCTN, PTBV hoặc ESG theo tài liệu. | `BCTN` |
| Kỳ báo cáo | Khoảng thời gian báo cáo đề cập. | `01/01/2024–31/12/2024` |

- **BCTN**: báo cáo thường niên, thường có tên *Annual Report*.
- **PTBV**: báo cáo phát triển bền vững, thường có tên *Sustainability Report*.
- **ESG**: báo cáo môi trường, xã hội và quản trị, thường có tên *ESG Report*.

**Chọn PTBV không tự chọn riêng phần 5 của PDF.** Nếu chỉ muốn phân tích một chương, hãy chọn khoảng trang chứa chương đó. Các báo cáo cùng mã công ty/năm cần thống nhất tên công ty, ngành và kỳ báo cáo; khoảng trang được giữ riêng cho từng file.

### 3. Chọn khoảng trang

App mặc định chọn **từ trang 1 đến trang cuối PDF**.

- **Từ trang**: chọn từ 1 đến trang cuối.
- **Đến trang**: chỉ cho chọn từ trang bắt đầu trở đi, không vượt quá trang cuối.
- Nếu đổi trang đầu vượt trang cuối đang chọn, app tự nâng trang cuối lên cho hợp lệ.
- Số trang tính theo thứ tự trong PDF, bắt đầu từ 1, không theo số in ở chân trang.

Ví dụ: PDF có 123 trang; chọn Từ trang = 40 thì Đến trang chỉ cho chọn 40–123. Muốn chỉ đọc trang PDF số 5, đặt cả hai ô bằng 5.

### 4. Chọn cách đếm và nơi lưu

Trong tab **Cài đặt & hướng dẫn** (hoặc **Cài đặt**):

- **Đếm cả nội dung trong bảng** mặc định được bật để giữ chữ trong bảng của các trang đã chọn. Nếu phương pháp nghiên cứu yêu cầu loại bảng, có thể bỏ chọn mục này. Chế độ loại bảng chỉ lọc được các bảng có đường kẻ; trang OCR cần kiểm tra thủ công.
- **Nơi lưu kết quả** cho phép chọn thư mục đầu ra. Mỗi lần chạy tạo một thư mục riêng, giữ lại kết quả cũ.
- **Chuẩn bị OCR tự động** dùng khi bộ OCR chưa sẵn sàng hoặc cần tải bổ sung. Bản phát hành đã kèm OCR Việt/Anh.

`so_lan`, `so_tu` và các tần suất luôn được tính trên cùng phạm vi trang và tùy chọn bảng.

### 5. Chạy phân tích

Trước khi chạy, vào **Cài đặt & hướng dẫn → Bộ từ điển** để chọn bộ cần dùng. Bộ **Mặc định** được giữ nguyên; bấm **Sao chép thành bộ riêng** để tùy chỉnh:

1. Đặt tên bộ theo nhu cầu nghiên cứu. Chọn một mục để sửa hoặc bấm **Mục mới**.
2. Chọn nhóm SYMB/SUBST/E5, tên mục và nhập các biến thể tiếng Anh/Việt, mỗi dòng một cụm. Bỏ chọn **Dùng** để tạm tắt mục.
3. Bấm **Áp dụng mục** trước khi chuyển sang mục khác; sau đó **Lưu bộ từ điển**. Mẫu tiếng Anh nâng cao là regex có sẵn; giữ nguyên nếu chưa cần sửa.
4. Dùng **Thử đếm** với đoạn văn và ngôn ngữ đã chọn để kiểm tra các mục đã áp dụng.

Các nút **Mục mới / Áp dụng mục / Xóa mục / Lưu bộ từ điển** luôn nằm ở góc phải dưới cửa sổ quản lý, kể cả khi cuộn nội dung. Khi cửa sổ hẹp, các nút tự xuống hàng. App hiện thông báo sau từng thao tác thành công, phân biệt rõ thay đổi đang chỉnh với thay đổi đã lưu xuống máy.

**Xuất Excel / mẫu** tạo file mở đầu bằng sheet **Hướng dẫn**, giải thích cách nhập từng cột, ví dụ biến thể Anh/Việt, regex tùy chọn và một dòng mẫu hoàn chỉnh. Chuyển sang sheet **Từ điển** để sửa dữ liệu; ví dụ trong hướng dẫn không tự được nhập. Trong Excel, dùng Alt+Enter để tách các biến thể trong cùng ô; cột `bat` nhận 1 hoặc 0. **Nhập Excel** tạo một bộ mới, giữ nguyên các bộ cũ. App chặn tên mục trùng trong cùng nhóm và báo biến thể trùng để rà soát; cùng đoạn chữ vẫn chỉ được đếm một lần, ưu tiên cụm dài.

Các bộ cá nhân lưu tại `tu_dien_ca_nhan/` trong thư mục dữ liệu (bản exe: `du_lieu/tu_dien_ca_nhan/`). App nhớ bộ đã chọn. Mỗi lần phân tích lưu `tu_dien_da_dung.json` cùng kết quả; sheet **Chỉ số** có `bo_tu_dien` và `ma_tu_dien` (SHA-256) để đối chiếu. Sửa từ điển không thay đổi kết quả cũ; cần chạy lại để áp dụng.

Khi chạy dòng lệnh, dùng `--dictionary duong_dan.json` với bản chụp JSON của một lần chạy; bỏ tùy chọn này để dùng bộ mặc định.

Bấm **Bắt đầu phân tích**, theo dõi tab **Kết quả phân tích** và **Nhật ký xử lý**. Chờ xử lý hoàn tất trước khi đóng app. Một PDF bị lỗi không ngăn các PDF khác tiếp tục được xử lý; nhật ký ghi rõ file và nguyên nhân lỗi.

### 6. Mở kết quả Excel

Bấm **Mở file Excel** sau khi phân tích. Nếu máy có Microsoft Excel, app ưu tiên mở trực tiếp bằng Excel. Khi chưa chạy trong phiên hiện tại, nút này cũng cho phép chọn một file `.xlsx` đã lưu.

| Sheet | Nội dung |
|---|---|
| Tổng hợp | Bảng 21 cột; một dòng mỗi doanh nghiệp theo quy tắc chọn báo cáo. |
| Chỉ số | Khoảng trang, tổng từ, tần suất các nhóm, tỷ lệ SUBST và phạm vi văn bản của từng báo cáo. |
| Từ khóa | Số lần xuất hiện và tần suất trên 1.000 từ/âm tiết của từng mục từ khóa. |
| Chủ đề LDA | Chủ đề, các từ khóa, nhãn gợi ý và tỷ trọng nếu đủ dữ liệu. |
| Từ khóa theo trang | Số lần từ khóa xuất hiện trên từng trang PDF; chỉ ghi các mục có xuất hiện. |

Để kiểm tra một số đếm, lọc mã công ty, năm, loại báo cáo, nhóm và từ khóa trong sheet **Từ khóa theo trang**. Cộng `so_lan` của các trang sẽ bằng số đếm tổng trong sheet **Từ khóa**.

### 7. Tự lưu, cuộn và cập nhật app

App tự lưu sau một khoảng dừng nhập ngắn và khi đóng. Mở lại sẽ khôi phục PDF, thông tin nhập dở, khoảng trang, cài đặt và kết quả gần nhất.

- Đặt chuột trên vùng muốn cuộn rồi lăn: tab, bảng hoặc nhật ký.
- Giữ **Shift + lăn chuột** để cuộn ngang bảng, hoặc kéo thanh cuộn ngang.
- Có thể dùng phím Tab để di chuyển giữa các ô nhập.
- Nếu PDF đã bị chuyển chỗ, chọn dòng tương ứng rồi bấm **Chọn lại PDF**. Thông tin công ty đã nhập vẫn được giữ.
- Khi cập nhật bản `.exe`, đóng app trước và giữ lại thư mục `du_lieu` cùng các PDF gốc. Bản portable cần cập nhật cả thư viện đi kèm.

## Giải thích các chỉ số

| Cột | Ý nghĩa |
|---|---|
| `so_tu` | Tổng số từ sau xử lý trong phạm vi đã chọn; với tiếng Việt hiện tính theo âm tiết. |
| `so_lan` | Số lần một mục từ khóa/cụm từ khóa được tính theo từ điển. |
| `tren_1000` | `so_lan / so_tu × 1.000`, dùng để so sánh báo cáo dài ngắn khác nhau. |
| `SYMB_1000` | Tổng số lần các từ khóa SYMB trên 1.000 từ/âm tiết. |
| `SUBST_1000` | Tổng số lần các từ khóa SUBST trên 1.000 từ/âm tiết. |
| `E5_1000` | Tổng số lần các từ khóa E5 trên 1.000 từ/âm tiết. |
| `SUBST_RATIO` | `SUBST / (SUBST + SYMB)`; để trống nếu mẫu số bằng 0. |
| `pham_vi_van_ban` | Cho biết lần chạy có tính nội dung bảng hay không. |

Ví dụ: một mục từ khóa xuất hiện 20 lần trong 10.000 từ sau xử lý thì `tren_1000 = 2`. Đây là tần suất chuẩn hóa, không phải 2%.

## App hoạt động như thế nào?

```text
PDF và khoảng trang do người dùng chọn
        ↓
Trích chữ trực tiếp / OCR trang ít chữ
        ↓
Giữ hoặc loại chữ trong bảng theo cài đặt
        ↓
Chuẩn hóa văn bản, xác định ngôn ngữ
        ↓
Đếm từ khóa theo từng trang, tính chỉ số
        ↓
Khám phá chủ đề bằng LDA nếu đủ dữ liệu
        ↓
Xuất Excel, CSV, JSON và báo cáo kiểm tra
```

### Trích chữ và OCR

App dùng `pdfplumber` để đọc lớp chữ trong PDF. Trang có ít hơn 30 từ trích được sẽ được chuyển thành ảnh bằng PDFium và nhận dạng bằng Tesseract với bộ tiếng Việt/Anh. Bộ đọc PDF và OCR đã có trong bản Windows đóng gói.

### Làm sạch và đếm từ

App chuẩn hóa Unicode, chuyển chữ về chữ thường, nối từ bị ngắt dòng bằng gạch nối, bỏ URL/email, chữ số và dấu câu. Ngôn ngữ được nhận diện bằng tỷ lệ ký tự có dấu tiếng Việt để chọn bộ mẫu đếm tương ứng.

Bộ từ điển mặc định có **25 mục SYMB, 14 SUBST và 27 E5**, kèm các biến thể hoặc cụm từ tiếng Việt. Bộ cá nhân có thể thay đổi số mục và biến thể. App khớp nguyên từ, ưu tiên cụm dài và không đếm chồng cùng một đoạn chữ. Ví dụ, `assessment` và `assessments` được gộp vào Assessment; `pre-assessment` được tính riêng cho Pre-assessment. Mỗi trang được đếm độc lập để tránh ghép nhầm cụm từ qua ranh giới trang.

### Phân tích chủ đề LDA

App dùng scikit-learn để phân tích riêng hai nhóm ngôn ngữ. Mỗi trang có ít nhất 40 từ/âm tiết sau làm sạch được xem là một văn bản. Nhóm dưới 6 trang đạt điều kiện sẽ được bỏ qua.

App lọc từ bằng `min_df=3`, `max_df=0.5`, thử số chủ đề từ 4 đến 12 và chọn theo điểm UMass được tính trong chương trình. Nhãn chủ đề là gợi ý tự động cần người dùng rà soát; việc bỏ qua LDA không làm mất bảng đếm từ khóa của các báo cáo xử lý thành công.

## Dữ liệu được lưu ở đâu?

Với bản `.exe`, phiên làm việc và kết quả mặc định nằm trong thư mục **`du_lieu` cạnh file chạy**:

```text
ESGStudio-Windows-x64.exe
du_lieu/
  .app_state/session.json
  ket_qua/
    thu_muc_moi_lan_chay/
```

Nếu đã chọn nơi xuất khác, kết quả nằm ở thư mục được chọn. App nhớ đường dẫn PDF gốc, không tự sao chép PDF gốc vào phiên lưu.

PDF được xử lý trên máy, không gửi nội dung ra dịch vụ bên ngoài. Chỉ cần Internet nếu phải tải bổ sung hoặc sửa bộ OCR bằng chức năng chuẩn bị tự động.

## Câu hỏi thường gặp

### Vì sao Ctrl+F có số khác `so_lan`?

Kiểm tra đúng PDF, khoảng trang và tùy chọn bảng. App khớp nguyên từ, gộp biến thể và ưu tiên cụm dài, nên kết quả có thể khác tìm chuỗi con. OCR cũng có thể sai hoặc thiếu chữ. Dùng sheet **Từ khóa theo trang** để xác định trang bị lệch.

### Đổi cách đếm rồi mà Excel vẫn như cũ?

File kết quả cũ không tự tính lại. Bấm **Bắt đầu phân tích** để tạo kết quả mới, rồi mở Excel của lần chạy mới. Cột `pham_vi_van_ban` trong sheet Chỉ số giúp phân biệt cách đếm.

### LDA vi báo “Bỏ qua”, LDA en báo “OK” là sao?

Nhóm tiếng Việt chưa đủ dữ liệu để chạy LDA, còn nhóm tiếng Anh đã chạy được. Các bảng đếm từ khóa vẫn được xuất cho báo cáo xử lý thành công. Nếu tài liệu tiếng Việt bị xếp vào tiếng Anh thì cần rà soát nhận diện ngôn ngữ.

### Vì sao Excel không mở hoặc không ghi được?

Kiểm tra file còn tồn tại, nơi lưu có quyền ghi và máy có ứng dụng đọc `.xlsx`. Nếu file đang bị Excel giữ, đóng file đó rồi thử lại. Khi mở một kết quả mới có cùng tên với workbook đang mở, đóng workbook cũ trước.

## Giới hạn cần hiểu

- OCR và trích chữ có thể sai với ảnh mờ, chữ nhỏ hoặc bố cục nhiều cột.
- Chế độ loại bảng không đảm bảo loại chính xác mọi bảng, đặc biệt trên trang OCR.
- Báo cáo song ngữ hiện được xếp vào một ngôn ngữ; cần kiểm tra việc nhận diện và từ khóa bị bỏ sót.
- SYMB/SUBST/E5 là nhóm từ khóa. Tần suất hoặc nhãn LDA chưa đủ để tự kết luận doanh nghiệp công bố hình thức hay thực chất.
- Từ điển và cách triển khai tài liệu phương pháp chưa được xác minh độc lập đầy đủ. Khi dùng cho nghiên cứu, cần thống nhất quy tắc và đối chiếu một mẫu bằng tay.

## Chạy từ mã nguồn

Cần Python 3.10 trở lên với Tkinter. Trên Windows, chạy `Cai_dat_app.cmd` để cài các thư viện và chuẩn bị OCR, sau đó mở `Mo_app.cmd`. Mã nguồn và bản `.exe` có cùng luồng sử dụng; dữ liệu của bản mã nguồn nằm trong thư mục dự án.

Muốn đóng gói lại, chạy `Dong_goi_exe.cmd` cho bản portable hoặc `Dong_goi_exe.cmd onefile` cho bản một file. Thông tin chi tiết còn được giữ ở [GIOI_THIEU_APP.md](GIOI_THIEU_APP.md) và [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md).
