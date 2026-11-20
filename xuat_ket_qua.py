"""Xuất CSV UTF-8 BOM, JSON, TSV 21 cột và bằng chứng để kiểm tra."""
import csv
import json
import re
from collections import Counter
from pathlib import Path
from dem_tu import dem_tu
from excel_output import create_excel
from dictionary_store import default_dictionary, dictionary_groups, save_dictionary, fingerprint

HEADERS = ['STT','Topic chung','Tên bài báo (có thể bỏ link doi r đổi tên)','Tạp chí xuất bản','SSCI','Năm','Tác giả',
           'Câu hỏi nghiên cứu','Mẫu','Cỡ mẫu','Quốc gia','Phương pháp thu thập dữ liệu','Foundation theory',
           'Mô hình nghiên cứu','Biến độc lập','Biến phụ thuộc','Kết quả','Limitations','Đề xuất trong tương lai',
           'Đóng góp gì cho bài mình','Tên người làm']
FIELDS = ['ma','nam','loai','ngon_ngu','trang_dau','trang_cuoi','so_trang','so_tu','SYMB_1000','SUBST_1000','E5_1000','SUBST_RATIO','pham_vi_van_ban','bo_tu_dien','ma_tu_dien']

def write_csv(path, fields, rows, delimiter=','):
    with open(path, 'w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore', delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)

def export(reports, lda, out, errors, dictionary=None):
    dictionary = default_dictionary() if dictionary is None else dictionary
    groups = dictionary_groups(dictionary)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    save_dictionary(out / 'tu_dien_da_dung.json', dictionary)
    for report in reports:
        report['bo_tu_dien'] = dictionary['name']
        report['ma_tu_dien'] = fingerprint(dictionary)
    write_csv(out/'chi_so_doanh_nghiep.csv', FIELDS, reports)
    keywords = []
    for r in reports:
        for (group, name), count in r['counts'].items():
            keywords.append({'ma': r['ma'], 'nam': r['nam'], 'loai': r['loai'], 'nhom': group,
                             'tu_khoa': name, 'so_lan': count, 'tren_1000': count*1000/r['so_tu'] if r['so_tu'] else 0})
    write_csv(out/'tan_suat_tu_khoa.csv', ['ma','nam','loai','nhom','tu_khoa','so_lan','tren_1000'], keywords)
    per_page = []
    for report in reports:
        for page, values in report.get('page_counts', {}).items():
            for (group, name), count in values.items():
                if count:
                    per_page.append({'ma': report['ma'], 'nam': report['nam'], 'loai': report['loai'],
                                     'trang': page, 'nhom': group, 'tu_khoa': name, 'so_lan': count})
    write_csv(out/'tu_khoa_theo_trang.csv', ['ma','nam','loai','trang','nhom','tu_khoa','so_lan'], per_page)
    # Có nhiều báo cáo cùng mã: thêm năm/loại để tránh ghi đè cột.
    ticker_counts = Counter(r['ma'] for r in reports)
    columns = [r['ma'] if ticker_counts[r['ma']] == 1 else r['id'] for r in reports]
    wide = []
    for key in (reports[0]['counts'] if reports else {}):
        row = {'nhom': key[0], 'tu_khoa': key[1]}
        for col, report in zip(columns, reports):
            row[col] = report['counts'][key]*1000/report['so_tu'] if report['so_tu'] else 0
        row['trung_binh'] = sum(row[c] for c in columns)/len(columns)
        wide.append(row)
    write_csv(out/'bang_tu_khoa_kieu_bai_bao.csv', ['nhom','tu_khoa',*columns,'trung_binh'], sorted(wide, key=lambda r: -r['trung_binh']))
    (out/'chu_de_lda.json').write_text(json.dumps(lda, ensure_ascii=False, indent=2), encoding='utf-8')
    topic_rows = []
    for language, group in lda['nhom'].items():
        for topic in group['chu_de']:
            base = {'ngon_ngu': language, **topic, 'tu_khoa': ', '.join(topic['tu_khoa']), 'k': group['k'], 'umass': group['umass']}
            topic_rows.append({**base, 'bao_cao': 'TOAN_BO', 'ty_trong': topic['ty_trong']})
            for owner, proportions in group['ty_trong_bao_cao'].items():
                topic_rows.append({**base, 'bao_cao': owner, 'ty_trong': proportions[topic['chu_de']-1]})
    write_csv(out/'chu_de_lda.csv', ['ngon_ngu','k','umass','bao_cao','chu_de','ty_trong','tu_khoa','nhan','can_kiem_tra'], topic_rows)
    # Một doanh nghiệp: ưu tiên năm mới nhất, rồi PTBV > ESG > BCTN.
    selected = {}
    priority = {'PTBV': 3, 'ESG': 2, 'BCTN': 1}
    for r in sorted(reports, key=lambda r: (int(r['nam']), priority[r['loai']])):
        selected[r['ma']] = r
    sample = list(selected.values())
    sheet = []
    checks = ['Kết quả mô tả; không tự suy ra doanh nghiệp thực chất chỉ từ tần suất.',
              'LDA: nhãn cần người kiểm tra; bỏ qua được ghi rõ trong chu_de_lda.json.',
              'Xem cột pham_vi_van_ban để biết có tính nội dung bảng; bảng OCR không lọc chính xác được.', *errors, '']
    for r in reports:
        checks.append(f"{r['id']}: trang {r['trang_dau']}-{r['trang_cuoi']}; {r['so_tu']} từ/âm tiết; OCR={r['ocr']}; {r['selection']}; {r.get('pham_vi_van_ban', 'Chưa ghi phạm vi')}")
        top_e5 = [key for key, count in sorted(r['counts'].items(), key=lambda x: -x[1]) if key[0]=='E5' and count]
        examples = []
        # Chọn câu chứa các từ E5 thường gặp nhất; giữ số trang đối chiếu.
        for key in top_e5:
            for page in r['pages']:
                for sentence in re.split(r'(?<=[.!?])\s+|\n', page['raw']):
                    value = f"[trang {page['number']}] {sentence.strip()}"
                    if value not in examples and dem_tu(sentence, r['ngon_ngu'], groups).get(key, 0) > 0:
                        examples.append(value)
                    if len(examples) >= 5:
                        break
                if len(examples) >= 5:
                    break
            if len(examples) >= 5:
                break
        checks.extend(examples or ['Không có câu khớp E5.'])
        if len(examples) < 5:
            checks.append(f'Chỉ tìm được {len(examples)} câu ví dụ khác nhau.')
        checks.append('')
    for i, r in enumerate(sorted(sample, key=lambda x: x['ma']), 1):
        rank_ratio = None if r['SUBST_RATIO'] is None else 1+sum(x['SUBST_RATIO'] is not None and x['SUBST_RATIO']>r['SUBST_RATIO'] for x in sample)
        rank_e5 = 1+sum(x['E5_1000']>r['E5_1000'] for x in sample)
        top = [(name, n) for (g, name), n in sorted(r['counts'].items(), key=lambda x: -x[1]) if g=='E5' and n][:2]
        group = lda['nhom'][r['ngon_ngu']]
        proportions = group['ty_trong_bao_cao'].get(r['id'])
        topic = 'LDA chưa đủ dữ liệu'
        if proportions:
            index = max(range(len(proportions)), key=lambda j: proportions[j])
            topic = f"LDA {index+1} ({group['chu_de'][index]['nhan']}): {proportions[index]:.1%}; nhãn cần kiểm tra"
        ratio = 'không xác định (SYMB+SUBST=0)' if rank_ratio is None else f"{r['SUBST_RATIO']:.2%}, hạng {rank_ratio}/{len(sample)}"
        result = f"SUBST_RATIO: {ratio}; E5_1000: {r['E5_1000']:.3f}, hạng {rank_e5}/{len(sample)}; E5 nhiều nhất: {', '.join(f'{n} ({c})' for n,c in top) or 'không có'}; {topic}"
        flags = []
        flags.append('Phạm vi đếm: ' + r.get('pham_vi_van_ban', 'Chưa ghi phạm vi'))
        if r['ocr']: flags.append('Có trang scan/OCR; có thể sai nhận dạng và còn chữ trong bảng')
        if r['so_trang'] < 10: flags.append('Phần phân tích dưới 10 trang')
        if r['ky_bao_cao'] != r['nam']: flags.append(f"Kỳ báo cáo cần kiểm tra, có thể lệch năm dương lịch: {r['ky_bao_cao']}")
        if r['ngon_ngu']=='vi': flags.append('Tiếng Việt: tần suất tính theo âm tiết')
        if sum(x['ma']==r['ma'] for x in reports)>1: flags.append(f"Có nhiều báo cáo: TSV chọn {r['id']}; xếp hạng trên một báo cáo mỗi doanh nghiệp")
        values = [i,r['nganh'],f"{r['loai']} {r['nam']} – {r['ten_cong_ty']}",
                  'Không có (báo cáo do doanh nghiệp tự công bố)','Không áp dụng',r['nam'],
                  f"{r['ten_cong_ty']} ({r['ma']})",f"Công bố E5 của {r['ma']} mang tính hình thức hay thực chất?",
                  f"{r['selection']}; {'tiếng Việt' if r['ngon_ngu']=='vi' else 'tiếng Anh'}",
                  f"{r['so_trang']} trang, khoảng {r['so_tu']} từ/âm tiết",'Việt Nam',
                  'Người dùng tải PDF; trích phần PTBV; '+('có OCR' if r['ocr'] else 'không dùng OCR'),
                  'Lý thuyết tính chính danh, lý thuyết thể chế; phân loại symbolic – substantive',
                  f"Đếm từ khóa và LDA; bộ từ điển: {dictionary['name']} (xem tu_dien_da_dung.json). Bộ mặc định tham khảo Ji et al. 2024; ESRS E5; Hadro et al.",
                  'Không có (phân tích mô tả)','Tỷ lệ từ substantive; số thuật ngữ E5 trên 1.000 từ',
                  result,'; '.join(flags),'','','']
        sheet.append(dict(zip(HEADERS, [re.sub(r'[\t\r\n]+', ' ', str(v)) for v in values])))
    write_csv(out/'google_sheet.tsv', HEADERS, sheet, '\t')
    (out/'bao_cao_kiem_tra.txt').write_text('\n'.join(checks), encoding='utf-8')
    create_excel(out)
