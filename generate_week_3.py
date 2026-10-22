# -*- coding: utf-8 -*-
import os
import sys
import io

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def apply_document_page_setup(doc):
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)
        sec.page_width = Inches(8.27)   # A4
        sec.page_height = Inches(11.69) # A4

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="94A3B8", sz="6", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_header_info_table(doc):
    t = doc.add_table(rows=8, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="94A3B8", sz="6")
    
    info_data = [
        ("Sinh viên thực hiện", "Trần Văn Hoàng"),
        ("Mã số sinh viên (MSSV)", "0034467"),
        ("Lớp chuyên ngành", "67CS – Khóa K67"),
        ("Đơn vị thực tập", "Công ty TNHH Nền tảng chuyển đổi số Việt Nam"),
        ("Bộ phận công tác", "eGov – Khối Chính phủ số"),
        ("Cán bộ hướng dẫn tại đơn vị", "Đào Đức Văn"),
        ("Dự án tham gia", "Hệ thống báo cáo điện tử eForm"),
        ("Đề tài nghiên cứu", "Nghiên cứu và ứng dụng AI xây dựng Module Import file Excel thông minh, tự động ánh xạ dữ liệu cho hệ thống Báo cáo thống kê eForm.")
    ]
    
    col_widths = [Inches(2.1), Inches(4.6)]
    for i, (label, val) in enumerate(info_data):
        row = t.rows[i]
        row.cells[0].width = col_widths[0]
        row.cells[1].width = col_widths[1]
        
        set_cell_background(row.cells[0], "F8FAFC")
        set_cell_margins(row.cells[0], top=70, bottom=70, left=120, right=120)
        set_cell_margins(row.cells[1], top=70, bottom=70, left=120, right=120)
        
        p0 = row.cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r0 = p0.add_run(label)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(11.5)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(30, 41, 59)
        
        p1 = row.cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1 = p1.add_run(val)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11.5)
        if label in ["Sinh viên thực hiện", "Mã số sinh viên (MSSV)", "Cán bộ hướng dẫn tại đơn vị"]:
            r1.font.bold = True
        r1.font.color.rgb = RGBColor(15, 23, 42)
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(2)
    p_sp.paragraph_format.space_after = Pt(6)

def add_title(doc, week_num, date_range, subtitle):
    p0 = doc.add_paragraph()
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run(f"BÁO CÁO THỰC TẬP TUẦN {week_num}")
    r0.font.name = "Times New Roman"
    r0.font.size = Pt(18)
    r0.font.bold = True
    r0.font.color.rgb = RGBColor(15, 23, 42)
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(2)
    
    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_date = p_date.add_run(f"({date_range})")
    r_date.font.name = "Times New Roman"
    r_date.font.size = Pt(11.5)
    r_date.font.italic = True
    r_date.font.color.rgb = RGBColor(100, 116, 139)
    p_date.paragraph_format.space_before = Pt(0)
    p_date.paragraph_format.space_after = Pt(4)
    
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run(subtitle.upper())
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(13)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(2, 132, 199)
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(14)

def add_h1(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(5)
    return p

def add_h2(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 41, 59)
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(3)
    return p

def add_h3(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.italic = True
    r.font.color.rgb = RGBColor(51, 65, 85)
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    return p

def add_p(doc, text, bold_prefix="", italic=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    
    if bold_prefix:
        rb = p.add_run(bold_prefix + " ")
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(12)
        rb.font.bold = True
        rb.font.color.rgb = RGBColor(15, 23, 42)
        
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.italic = italic
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_bullet(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.2
    
    if bold_prefix:
        rb = p.add_run(bold_prefix + ": ")
        rb.font.name = "Times New Roman"
        rb.font.size = Pt(12)
        rb.font.bold = True
        rb.font.color.rgb = RGBColor(15, 23, 42)
        
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_image_figure(doc, img_path, caption):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(6.2))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(8)
        r_cap = p_cap.add_run(caption)
        r_cap.font.name = "Times New Roman"
        r_cap.font.size = Pt(10.5)
        r_cap.font.italic = True
        r_cap.font.bold = True
        r_cap.font.color.rgb = RGBColor(51, 65, 85)
    else:
        print(f"Lưu ý: Không tìm thấy ảnh {img_path}")

def add_custom_table(doc, headers, rows_data, col_widths=None):
    t = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="94A3B8", sz="6")
    
    # Header
    hdr_row = t.rows[0]
    for j, h in enumerate(headers):
        if col_widths:
            hdr_row.cells[j].width = col_widths[j]
        set_cell_background(hdr_row.cells[j], "E2E8F0")
        set_cell_margins(hdr_row.cells[j], top=70, bottom=70, left=90, right=90)
        p = hdr_row.cells[j].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        
    # Rows
    for i, row_data in enumerate(rows_data):
        row = t.rows[i + 1]
        bg_col = "FFFFFF" if i % 2 == 0 else "F8FAFC"
        for j, val in enumerate(row_data):
            if col_widths:
                row.cells[j].width = col_widths[j]
            set_cell_background(row.cells[j], bg_col)
            set_cell_margins(row.cells[j], top=55, bottom=55, left=90, right=90)
            p = row.cells[j].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j > 0 else WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(str(val))
            r.font.name = "Times New Roman"
            r.font.size = Pt(10.5)
            if j == len(row_data) - 1 and str(val) in ["Đạt", "Hoàn thành", "Tốt", "Chính xác"]:
                r.font.bold = True
                r.font.color.rgb = RGBColor(16, 185, 129)
            elif j == len(row_data) - 1 and str(val) in ["Chưa đạt", "Lỗi"]:
                r.font.bold = True
                r.font.color.rgb = RGBColor(239, 68, 68)
            elif j == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(30, 41, 59)
            else:
                r.font.color.rgb = RGBColor(51, 65, 85)
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(2)
    p_sp.paragraph_format.space_after = Pt(6)

def generate_week_3():
    doc = Document()
    apply_document_page_setup(doc)
    
    add_title(
        doc,
        week_num=3,
        date_range="Từ ngày 17/08/2026 đến ngày 21/08/2026",
        subtitle="Tối ưu hóa phân hệ tra cứu – xuất báo cáo hàng loạt trên hệ thống eForm và thiết kế bộ dữ liệu định chuẩn cho Module Import Excel"
    )
    
    # --------------------------------------------------------------------------
    # I. THÔNG TIN CHUNG
    # --------------------------------------------------------------------------
    add_h1(doc, "I. THÔNG TIN CHUNG")
    add_header_info_table(doc)
    
    add_p(
        doc,
        "Tuần 3 là giai đoạn then chốt trong quá trình thực tập tốt nghiệp của em tại Khối Chính phủ số (eGov) thuộc Công ty TNHH Nền tảng chuyển đổi số Việt Nam. Trong tuần làm việc này, em thực hiện song song hai trọng tâm công tác: (1) Trực tiếp tham gia vào dự án chính của công ty – Hệ thống báo cáo điện tử eForm – để giải quyết các bài toán kỹ thuật cấp bách được phân công; và (2) Triển khai nghiên cứu chuyên sâu cho đề tài cá nhân – Module Import file Excel thông minh, tự động ánh xạ dữ liệu.",
        bold_prefix="Bối cảnh thực tập:"
    )
    add_p(
        doc,
        "Theo Nhật ký thực tập hàng ngày và phân công của cán bộ hướng dẫn Đào Đức Văn, nội dung công việc tuần 3 được phân bổ cụ thể: Thứ 2 họp giao ban tiến độ và tiếp nhận công việc; Thứ 3 khảo sát và sửa lỗi hiển thị sai đơn vị khởi tạo tại phân hệ Tra cứu báo cáo; Thứ 4 phát triển tính năng tải hàng loạt file báo cáo định dạng Excel trên giao diện tra cứu; Thứ 5 phân nhóm bố cục bảng và xây dựng tập dữ liệu huấn luyện – kiểm tra cho module Import Excel; Thứ 6 xây dựng bộ quy tắc định chuẩn (baseline) nhận diện cấu trúc bảng tính Excel.",
        bold_prefix="Mục tiêu trọng tâm tuần 3:"
    )
    
    # --------------------------------------------------------------------------
    # II. NỘI DUNG VÀ KẾT QUẢ THỰC HIỆN CHI TIẾT
    # --------------------------------------------------------------------------
    add_h1(doc, "II. NỘI DUNG VÀ KẾT QUẢ THỰC HIỆN CHI TIẾT")
    
    # --------------------------------------------------------------------------
    # MỤC 1: QUÁ TRÌNH THỰC TẬP TẠI CÔNG TY
    # --------------------------------------------------------------------------
    add_h2(doc, "MỤC 1. QUÁ TRÌNH THỰC TẬP TẠI CÔNG TY: THỰC HIỆN CÁC NHIỆM VỤ DỰ ÁN CHÍNH (HỆ THỐNG EFORM)")
    
    # 1.1. Họp giao ban
    add_h3(doc, "1.1. Họp giao ban tiến độ dự án eForm và tiếp nhận nhiệm vụ tuần 3 (Thứ 2, 17/08/2026)")
    add_p(
        doc,
        "Vào sáng Thứ 2 (17/08/2026), em tham dự buổi họp giao ban kỹ thuật định kỳ đầu tuần của Khối Chính phủ số (eGov) dưới sự chủ trì của anh Đào Đức Văn cùng toàn thể các kỹ sư phát triển phân hệ eForm. Thông qua cuộc họp, em đã lắng nghe và nắm bắt sâu sắc bối cảnh thực tế của hệ thống báo cáo điện tử eForm – nền tảng số hóa nghiệp vụ báo cáo thống kê đang phục vụ cho Bộ Tư pháp, các Sở Tư pháp tỉnh/thành phố và hệ thống các đơn vị cấp cơ sở (xã, phường, thị trấn)."
    )
    add_p(
        doc,
        "Tại cuộc họp, nhóm phát triển ghi nhận các phản hồi nghiệp vụ từ người dùng thực tế và lãnh đạo đơn vị đối với phân hệ Tra cứu báo cáo. Anh Đào Đức Văn đã trực tiếp giao cho em phụ trách hai nhiệm vụ trọng tâm: rà soát, khắc phục triệt để lỗi hiển thị sai đơn vị khởi tạo báo cáo; và nghiên cứu, phát triển tính năng tải trọn gói hàng loạt file báo cáo Excel trực tiếp từ màn hình kết quả tìm kiếm."
    )
    add_p(
        doc,
        "Để chuẩn bị cho việc thực hiện các nhiệm vụ trên, em đã thực hiện rà soát quy trình quản lý mã nguồn của dự án trên hệ thống GitLab nội bộ của công ty. Toàn bộ mã nguồn dự án được tổ chức chặt chẽ theo các quy chuẩn doanh nghiệp: tạo nhánh tính năng riêng biệt cho từng đầu việc, đồng bộ mã nguồn thường xuyên, cam kết lịch sử thay đổi rõ ràng và gửi yêu cầu hợp nhất nhánh (Merge Request) có kiểm duyệt kỹ lưỡng trước khi đưa vào nhánh chính thức."
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/gitlab_duan_chinh.png",
        "Hình 1. Quản lý quy trình phát triển và kiểm soát phiên bản mã nguồn dự án chính eForm trên hệ thống GitLab nội bộ."
    )
    
    # 1.2. Sửa lỗi tra cứu
    add_h3(doc, "1.2. Khảo sát luồng dữ liệu, gỡ lỗi và sửa lỗi hiển thị sai đơn vị khởi tạo báo cáo (Thứ 3, 18/08/2026)")
    add_p(
        doc,
        "Hiện tượng lỗi: Trên màn hình Tra cứu báo cáo của hệ thống eForm, cán bộ quản lý khi theo dõi danh sách báo cáo nộp lên phản ánh cột 'Đơn vị khởi tạo báo cáo' hiển thị không chính xác. Kết quả trên bảng dữ liệu luôn bị trùng lặp với tên của người tạo báo cáo, hoặc bị gán nhầm sang tên cơ quan cấp trên, làm mất đi tính minh bạch và gây khó khăn lớn cho công tác tổng hợp số liệu theo địa bàn.",
        bold_prefix="Bối cảnh và vấn đề phát sinh:"
    )
    add_p(
        doc,
        "Để tìm hiểu nguyên nhân cốt lõi của sự cố, em đã tiến hành các bước khảo sát và phân tích luồng dữ liệu kỹ thuật:",
        bold_prefix="Quy trình debug và phân tích kỹ thuật:"
    )
    add_bullet(
        doc,
        "Em sử dụng công cụ DevTools trên trình duyệt để đặt các điểm theo dõi (breakpoint) và bắt trực tiếp các gói tin trao đổi mạng giữa giao diện web và máy chủ. Qua phân tích, dữ liệu truyền đi từ bộ lọc tìm kiếm (các tiêu chí đơn vị, kỳ báo cáo, thời gian) hoàn toàn đầy đủ, tuy nhiên gói tin JSON phản hồi từ máy chủ đã mang sẵn giá trị sai lệch ở trường thông tin đơn vị khởi tạo.",
        "Kiểm tra giao diện và gói tin API"
    )
    add_bullet(
        doc,
        "Sau khi xác định lỗi phát sinh từ phía máy chủ, em truy vết sâu vào tầng điều khiển và dịch vụ xử lý dữ liệu tra cứu của Backend (.NET). Tại đây, em phát hiện thuật toán bóc tách chuỗi đường dẫn phân cấp phòng ban đang xử lý chưa chuẩn xác: thay vì trích xuất định danh cơ quan ban hành gốc, mã nguồn lại thực hiện cắt chuỗi và gán nhầm thông tin của người lập biểu vào trường đơn vị khởi tạo, dẫn tới việc kết quả trả về luôn hiển thị tên tài khoản cá nhân thay vì cơ quan, đơn vị nộp báo cáo.",
        "Rà soát tầng nghiệp vụ Backend (.NET)"
    )
    add_p(
        doc,
        "Em đã điều chỉnh lại logic trích xuất dữ liệu tại tầng nghiệp vụ Backend: truy vấn chính xác đối tượng cơ quan ban hành từ danh bạ phòng ban theo đúng định danh đơn vị khởi tạo, tách biệt rạch ròi giữa hai trường thông tin độc lập là đơn vị khởi tạo báo cáo và người khởi tạo báo cáo. Đồng thời, em chuẩn hóa lại các tham số mặc định của bộ lọc tìm kiếm trên giao diện người dùng để đảm bảo kết quả truy vấn luôn đồng nhất và chính xác tuyệt đối.",
        bold_prefix="Giải pháp xử lý kỹ thuật:"
    )
    add_p(
        doc,
        "Sau khi hiệu chỉnh mã nguồn và kiểm thử trên môi trường thử nghiệm thực tế của hệ thống eForm (https://baocao-btp.demozone.vn:8443/), chức năng tra cứu đã hoạt động chuẩn xác 100%. Danh sách kết quả hiển thị rành mạch, đúng đắn tên từng cơ quan, đơn vị nộp biểu (ví dụ: UBND Phường Giảng Võ, UBND Phường Mường Lay, UBND Phường Mường Thanh, Sở Tư pháp Tỉnh Điện Biên, Cục Kế hoạch - Tài chính...) tương ứng với từng cán bộ báo cáo cụ thể.",
        bold_prefix="Kết quả thực tế ghi nhận:"
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/01_minh_chung_tra_cuu_bao_cao.png",
        "Hình 2. Giao diện Tra cứu báo cáo sau khi khắc phục lỗi: cột Đơn vị khởi tạo báo cáo hiển thị chính xác từng cơ quan, đơn vị ban hành."
    )
    
    # 1.3. Viết tính năng tải toàn bộ file excel
    add_h3(doc, "1.3. Phát triển tính năng tải hàng loạt file báo cáo định dạng Excel tại màn hình Tra cứu (Thứ 4, 19/08/2026)")
    add_p(
        doc,
        "Trước đây, hệ thống eForm chỉ hỗ trợ người dùng xuất file Excel cho từng báo cáo đơn lẻ khi mở trực tiếp biểu mẫu đó. Khi cán bộ tổng hợp cần số liệu của hàng chục đơn vị trực thuộc, họ buộc phải mở từng báo cáo một và bấm nút xuất từng lần rất mất thời gian. Yêu cầu cấp bách đặt ra cho em là phát triển tính năng xuất hàng loạt file báo cáo định dạng Excel trực tiếp ngay trên bảng danh sách kết quả tra cứu.",
        bold_prefix="Yêu cầu nghiệp vụ và sự cần thiết:"
    )
    add_p(
        doc,
        "Em đã phân tích kiến trúc hệ thống và xây dựng giải pháp toàn diện bao gồm cả tầng giao diện người dùng và tầng xử lý nghiệp vụ phía máy chủ:",
        bold_prefix="Giải pháp kỹ thuật và kiến trúc triển khai:"
    )
    add_bullet(
        doc,
        "Em thiết kế thêm nút chức năng 'Xuất file' dạng danh mục đổ xuống (dropdown) tại thanh tiêu đề bảng kết quả. Menu cung cấp các tùy chọn thao tác linh hoạt: 'Tải tất cả Excel' (có áp dụng cấu hình hạn mức an toàn hệ thống), 'Tải bản ghi đã chọn' và 'Xuất danh sách' theo các định dạng văn phòng phổ biến (Excel, Word, PDF).",
        "Giao diện menu xuất file đa năng"
    )
    add_bullet(
        doc,
        "Tích hợp thêm cơ chế chọn bản ghi bằng ô đánh dấu (checkbox): ô đánh dấu tổng tại tiêu đề cột STT cho phép chọn nhanh tất cả các dòng trên trang hiện tại, kết hợp các ô đánh dấu trên từng dòng dữ liệu. Danh sách các mã định danh báo cáo được chọn được lưu trữ và đồng bộ liên tục trong cấu trúc tập hợp (Set) tại bộ nhớ trình duyệt, đảm bảo không bị mất trạng thái khi người dùng thao tác.",
        "Cơ chế chọn bản ghi linh hoạt"
    )
    add_bullet(
        doc,
        "Xây dựng hộp thoại tiến trình xử lý tải ngầm trên nền tảng web: cán bộ có thể chủ động thu nhỏ cửa sổ tiến độ xuống góc màn hình để tiếp tục tra cứu các tác vụ khác mà không bị đóng băng giao diện. Hệ thống tích hợp cơ chế cảnh báo an toàn khi người dùng vô tình tải lại trang hoặc đóng tab trình duyệt trong lúc máy chủ đang nén tệp, bảo vệ tính toàn vẹn của tiến trình.",
        "Trải nghiệm tiến trình tải ngầm và an toàn"
    )
    add_bullet(
        doc,
        "Tái sử dụng tối đa logic xuất bảng tính Excel của từng biểu mẫu riêng lẻ sẵn có trong hệ thống eForm nhằm bảo toàn tuyệt đối các công thức tính toán và cấu trúc ô gộp theo đúng quy định pháp lý; xây dựng dịch vụ tiếp nhận danh sách các mã định danh báo cáo theo lô để xử lý tuần tự, kiểm soát chặt chẽ dung lượng bộ nhớ.",
        "Tái sử dụng logic xuất bảng tính và xử lý theo lô"
    )
    add_bullet(
        doc,
        "Để bảo vệ tài nguyên máy chủ và tránh xung đột khi có nhiều người dùng thao tác đồng thời, mỗi yêu cầu xuất tệp được cấp phát một thư mục phiên làm việc tạm biệt lập mang mã định danh ngẫu nhiên (GUID). Các file Excel tạo ra được nạp vào luồng dữ liệu nhị phân (Stream) và đóng gói thành một tệp nén ZIP duy nhất có đóng dấu thời gian. Sau khi truyền tải thành công tệp ZIP về máy tính của người dùng, khối lệnh dọn dẹp an toàn tự động giải phóng bộ nhớ và xóa bỏ toàn bộ thư mục tạm trên máy chủ.",
        "Cơ chế đóng gói tệp nén ZIP và giải phóng bộ nhớ an toàn"
    )
    add_p(
        doc,
        "Tính năng đã hoàn thiện và thử nghiệm thành công trên môi trường thử nghiệm thực tế (https://baocao-btp.demozone.vn:8443/). Cán bộ có thể lựa chọn xuất toàn bộ hoặc chọn lọc các báo cáo theo nhu cầu, tệp nén ZIP chứa đầy đủ các bảng tính Excel chuẩn mực được tải về máy tính nhanh chóng chỉ sau một cú nhấp chuột.",
        bold_prefix="Kết quả thực tế ghi nhận:"
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/02_minh_chung_menu_xuat_excel.png",
        "Hình 3. Menu tùy chọn 'Xuất file' trên thanh công cụ bảng kết quả tra cứu báo cáo với các chế độ tải linh hoạt."
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/03_minh_chung_tai_ban_ghi_da_chon.png",
        "Hình 4. Thao tác tích chọn hàng loạt bản ghi qua checkbox và chuẩn bị xuất trọn gói tệp nén ZIP."
    )
    
    # --------------------------------------------------------------------------
    # MỤC 2: DỰ ÁN MODULE THỰC TẬP CÁ NHÂN
    # --------------------------------------------------------------------------
    add_h2(doc, "MỤC 2. DỰ ÁN THỰC TẬP CÁ NHÂN: NGHIÊN CỨU & XÂY DỰNG MODULE IMPORT EXCEL THÔNG MINH")
    
    # 2.1. Phân nhóm bố cục
    add_h3(doc, "2.1. Phân nhóm bố cục bảng tính và thiết kế tập dữ liệu huấn luyện – kiểm tra (Thứ 5, 20/08/2026)")
    add_p(
        doc,
        "Hệ thống báo cáo thống kê eForm tiếp nhận hơn 1.200 file Excel biểu mẫu thực tế thuộc 27 mã biểu nghiệp vụ khác nhau của ngành tư pháp. Qua quá trình khảo sát thực tế, em nhận thấy sự phân bố dữ liệu có độ lệch rất lớn: một số mẫu biểu như biểu 09a có tới 722 file, biểu 05b có 139 file, trong khi nhiều mẫu biểu khác chỉ có từ 2 đến 6 file. Đặc biệt, đa số các file trong cùng một mẫu biểu thực chất sử dụng chung một khuôn mẫu (template) và chỉ khác nhau về tên cơ quan nộp, thời gian báo cáo hoặc số liệu điền vào.",
        bold_prefix="Khảo sát kho dữ liệu biểu mẫu thực tế:"
    )
    add_p(
        doc,
        "Nếu thực hiện chia tập dữ liệu huấn luyện (Train) và kiểm tra (Test) theo cách ngẫu nhiên thông thường theo từng file, các biểu mẫu có chung khuôn mẫu sẽ xuất hiện đồng thời ở cả hai tập. Khi đó xảy ra hiện tượng rò rỉ dữ liệu (Data Leakage): mô hình học máy sẽ chỉ ghi nhớ các mẫu biểu quen thuộc thay vì học khả năng khái quát hóa cấu trúc bảng biểu, dẫn đến hiện tượng quá khớp (Overfitting) và phản ánh sai lệch năng lực thực tế của mô hình.",
        bold_prefix="Vấn đề rò rỉ dữ liệu (Data Leakage):"
    )
    add_p(
        doc,
        "Để giải quyết triệt để vấn đề rò rỉ dữ liệu, em đã nghiên cứu và hiện thực giải pháp phân tầng dữ liệu dựa trên đặc trưng hình học:",
        bold_prefix="Giải pháp trích xuất 'Vân tay bố cục' (Layout Fingerprint):"
    )
    add_bullet(
        doc,
        "Em xây dựng thuật toán phân tích tệp Excel để trích xuất các thông số hình học cốt lõi: số lượng cột dữ liệu, ma trận tọa độ các khối ô gộp tiêu đề (Merge Geometry), độ sâu phân tầng tiêu đề (Header Depth), định dạng các dòng mã chỉ tiêu và đặc trưng kiểu dữ liệu ô.",
        "Trích xuất đặc trưng hình học"
    )
    add_bullet(
        doc,
        "Băm (hash) các đặc trưng trên thành một mã định danh họ bố cục (Layout Family). Toàn bộ các file có cùng cấu trúc bảng biểu sẽ được gom chung vào một họ bố cục duy nhất.",
        "Gom cụm họ bố cục (Layout Families)"
    )
    add_bullet(
        doc,
        "Thực hiện phân chia tập dữ liệu dựa trên cấp độ họ bố cục theo tỷ lệ khoa học: 70% tập Huấn luyện (Train) để mô hình học các trọng số; 15% tập Thẩm định (Validation) để tinh chỉnh ngưỡng phân loại; 15% tập Kiểm tra (Test) để đánh giá độc lập; đồng thời thiết lập một tập Thử thách riêng biệt (Challenge Set) gồm các file có cấu trúc dị biệt (nhiều bảng trên một sheet, phân cấp dòng sâu). Toàn bộ các file thuộc cùng một họ bố cục được đảm bảo tuyệt đối chỉ nằm trong một phân tập duy nhất, ngăn ngừa hoàn toàn nguy cơ rò rỉ dữ liệu.",
        "Chiến lược phân chia tập dữ liệu nghiêm ngặt"
    )
    
    # 2.2. Baseline rules
    add_h3(doc, "2.2. Xây dựng bộ quy tắc định chuẩn (Baseline Heuristic Rules) nhận diện cấu trúc Excel (Thứ 6, 21/08/2026)")
    add_p(
        doc,
        "Trong các bài toán ứng dụng học máy và trí tuệ nhân tạo, việc xây dựng một bộ quy tắc định chuẩn dựa trên luật chuyên gia (Heuristic Baseline) là bước đi mang tính phương pháp luận bắt buộc. Bộ quy tắc này đóng vai trò làm mốc đối sánh chuẩn xác (Ground Truth Benchmark) để đo lường mức độ cải thiện của mô hình học máy tự động ở các giai đoạn sau, đồng thời giúp nhóm nghiên cứu nắm bắt toàn diện các góc cạnh dị biệt của bảng tính Excel.",
        bold_prefix="Ý nghĩa và mục tiêu xây dựng Baseline:"
    )
    add_p(
        doc,
        "Em đã thiết kế và hiện thực bộ quy tắc logic nhận diện các vùng chức năng chính trong bảng tính:",
        bold_prefix="Hệ thống quy tắc phân tách ranh giới bảng biểu:"
    )
    add_bullet(
        doc,
        "Dựa vào đặc trưng kiểu chữ in đậm, kích thước phông chữ nổi bật, các khối ô gộp ngang ôm trọn nhiều cột và sự xuất hiện của các từ khóa nhận diện hành chính (như 'Biểu số', 'Báo cáo kết quả', 'Kính gửi').",
        "Quy tắc xác định vùng tiêu đề và thông tin đầu trang"
    )
    add_bullet(
        doc,
        "Nhận diện các mẫu định dạng ký hiệu thứ tự cột phổ biến trong biểu mẫu tư pháp như (1), (2), (3)... hoặc A, B, C... nằm liền kề ngay bên dưới khối tiêu đề để làm mốc phân định giữa phần nhãn cột và phần số liệu.",
        "Quy tắc nhận diện dòng mã chỉ tiêu"
    )
    add_bullet(
        doc,
        "Xác định ranh giới vùng dữ liệu dựa trên mật độ dày đặc của các ô chứa số thực, quy tắc căn lề phải, sự liên tục của đường viền ô (border) và phân tách ranh giới khi gặp các dòng chữ ký, người lập biểu hoặc ghi chú chân trang.",
        "Quy tắc khoanh vùng dữ liệu nghiệp vụ và chân trang"
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/Github_ai.png",
        "Hình 5. Quản lý cấu trúc tập dữ liệu, các kịch bản kiểm tra và bộ quy tắc định chuẩn trên hệ thống kho lưu trữ Git."
    )
    
    # 2.3. Thiết kế Backend độc lập
    add_h3(doc, "2.3. Thiết kế kiến trúc phân hệ Backend độc lập cho Module Import Excel")
    add_p(
        doc,
        "Nhằm hướng tới mục tiêu tích hợp an toàn vào hệ sinh thái phần mềm chính thức của Bộ Tư pháp (https://baocaothongke.moj.gov.vn/) trong tương lai mà tuyệt đối không gây xung đột mã nguồn hay làm gián đoạn các dịch vụ đang vận hành, em đã thiết kế Module Import Excel theo mô hình kiến trúc phân tầng độc lập trên nền tảng .NET Framework 4.8 / ASP.NET Web API 2:",
        bold_prefix="Nguyên tắc thiết kế kiến trúc phân hệ độc lập:"
    )
    add_bullet(
        doc,
        "Chứa các thực thể dữ liệu nghiệp vụ cốt lõi và các giao diện trừu tượng cho kho lưu trữ, hoàn toàn không phụ thuộc vào công nghệ cơ sở dữ liệu cụ thể.",
        "Tầng Miền dữ liệu (Domain)"
    )
    add_bullet(
        doc,
        "Hiện thực logic tiếp nhận workbook, chuẩn hóa cấu trúc bảng biểu thành dữ liệu JSON phân tầng và điều phối các dịch vụ xử lý dữ liệu.",
        "Tầng Nghiệp vụ ứng dụng (Application)"
    )
    add_bullet(
        doc,
        "Chịu trách nhiệm kết nối và lưu trữ an toàn các phiên làm việc vào cơ sở dữ liệu riêng biệt, bảo vệ tuyệt đối cấu trúc bảng dữ liệu cũ của eForm.",
        "Tầng Hạ tầng lưu trữ (Infrastructure)"
    )
    add_bullet(
        doc,
        "Tiếp nhận tệp Excel qua phương thức truyền tải đa phần (multipart/form-data), kiểm soát dữ liệu đầu vào và cung cấp tài liệu kiểm thử dịch vụ trực quan thông qua công cụ Swagger.",
        "Tầng Giao diện lập trình (API)"
    )
    add_image_figure(
        doc,
        "Docs/Tuần 3/swagger.png",
        "Hình 6. Giao diện Swagger hỗ trợ kiểm thử độc lập các dịch vụ tiếp nhận và chuẩn hóa dữ liệu của Module Import Excel."
    )
    
    # --------------------------------------------------------------------------
    # III. BẢNG TỔNG HỢP TIẾN ĐỘ VÀ KẾT QUẢ ĐẠT ĐƯỢC
    # --------------------------------------------------------------------------
    add_h1(doc, "III. BẢNG TỔNG HỢP TIẾN ĐỘ VÀ KẾT QUẢ ĐẠT ĐƯỢC THEO NHẬT KÝ THỰC TẬP")
    add_p(
        doc,
        "Dưới đây là bảng đối chiếu chi tiết giữa nội dung công việc được phân công và kết quả thực tế em đã hoàn thành trong Tuần 3, bám sát từng ngày theo đúng Nhật ký thực tập hàng ngày đã được cán bộ hướng dẫn phê duyệt:"
    )
    
    headers_w3 = ["STT", "Thời gian", "Nhiệm vụ công việc thực hiện", "Kết quả thực tế ghi nhận", "Đánh giá"]
    rows_w3 = [
        [
            "1",
            "Thứ 2\n17/08/2026",
            "Họp bàn về tiến độ dự án eForm và tiếp nhận các nhiệm vụ kỹ thuật trong tuần.",
            "Hiểu rõ tiến độ chung của hệ thống eForm, nắm vững yêu cầu phân hệ Tra cứu và nhận nhiệm vụ tuần 3.",
            "Hoàn thành"
        ],
        [
            "2",
            "Thứ 3\n18/08/2026",
            "Sửa lại tra cứu báo cáo đang hiển thị sai đơn vị khởi tạo báo cáo.",
            "Đã debug, sửa logic Backend và đồng bộ giao diện; phân hệ tra cứu hiển thị chuẩn xác 100% đơn vị khởi tạo.",
            "Hoàn thành"
        ],
        [
            "3",
            "Thứ 4\n19/08/2026",
            "Viết tính năng tải toàn bộ file báo cáo theo định dạng Excel ở tra cứu báo cáo.",
            "Hoàn thiện menu tải file, cơ chế chọn bản ghi qua checkbox và xuất hàng loạt file Excel nén ZIP an toàn.",
            "Hoàn thành"
        ],
        [
            "4",
            "Thứ 5\n20/08/2026",
            "Chia bộ dữ liệu theo nhóm bố cục bảng và chuẩn bị tập huấn luyện, kiểm tra cho module Import Excel.",
            "Hoàn thành giải pháp phân loại theo họ bố cục (layout family), ngăn chặn hoàn toàn rò rỉ dữ liệu giữa Train/Test.",
            "Hoàn thành"
        ],
        [
            "5",
            "Thứ 6\n21/08/2026",
            "Xây dựng bộ quy tắc baseline để nhận diện dòng tiêu đề, dòng dữ liệu và ranh giới bảng Excel.",
            "Xây dựng thành công bộ quy tắc định chuẩn dựa trên luật chuyên gia, làm mốc đối sánh chuẩn xác cho mô hình AI.",
            "Hoàn thành"
        ]
    ]
    add_custom_table(doc, headers_w3, rows_w3, [Inches(0.6), Inches(1.2), Inches(2.3), Inches(2.1), Inches(0.8)])
    
    # --------------------------------------------------------------------------
    # IV. KHÓ KHĂN GẶP PHẢI VÀ BÀI HỌC KINH NGHIỆM
    # --------------------------------------------------------------------------
    add_h1(doc, "IV. KHÓ KHĂN GẶP PHẢI VÀ BÀI HỌC KINH NGHIỆM")
    add_bullet(
        doc,
        "Hệ thống eForm quản lý danh mục phòng ban và phân cấp hành chính đa tầng rất đồ sộ (Bộ -> Cục/Vụ -> Sở -> Phòng -> Cấp Xã). Việc bóc tách đường dẫn chuỗi nếu không cẩn thận sẽ dễ nhầm lẫn giữa định danh đơn vị cha và người dùng thao tác. Qua việc trực tiếp debug và sửa lỗi này, em đã học được phương pháp truy vết dữ liệu khoa học bằng DevTools kết hợp kiểm tra nhật ký máy chủ để tìm ra nguyên nhân gốc rễ thay vì sửa chữa chắp vá.",
        "Kỹ năng xử lý dữ liệu phân cấp danh mục"
    )
    add_bullet(
        doc,
        "Khi thực hiện tải đồng thời nhiều báo cáo, nếu đọc toàn bộ tệp Excel vào bộ nhớ RAM trước khi nén ZIP thì máy chủ rất dễ bị quá tải khi nhiều người dùng cùng thao tác. Em đã nghiên cứu và ứng dụng cơ chế luồng nhị phân (Stream) kết hợp tạo thư mục phiên làm việc tạm có mã định danh GUID biệt lập, đảm bảo hiệu năng xử lý ổn định và dữ liệu tạm được dọn dẹp triệt để sau mỗi phiên.",
        "Tối ưu tài nguyên khi đóng gói tệp nén hàng loạt"
    )
    add_bullet(
        doc,
        "Bài toán trích xuất cấu trúc bảng biểu Excel có tính chất rất khác biệt so với các bài toán học máy thông thường do các tệp biểu mẫu thực tế thường sao chép từ cùng một khuôn mẫu gốc. Việc nhận diện nguy cơ rò rỉ dữ liệu (Data Leakage) và xây dựng thuật toán phân nhóm theo 'vân tay bố cục' (Layout Fingerprint) đã giúp em rèn luyện tư duy thiết kế tập dữ liệu khoa học, đảm bảo tính khách quan cho các nghiên cứu tiếp theo.",
        "Tư duy thiết kế tập dữ liệu học máy chuẩn mực"
    )
    
    # --------------------------------------------------------------------------
    # V. KẾT LUẬN VÀ KẾ HOẠCH TUẦN TIẾP THEO
    # --------------------------------------------------------------------------
    add_h1(doc, "V. KẾT LUẬN VÀ KẾ HOẠCH TUẦN TIẾP THEO")
    add_p(
        doc,
        "Trong Tuần 3, em đã hoàn thành 100% khối lượng công việc được giao theo đúng kế hoạch học tập và nhật ký thực tập. Cả hai mảng công việc – hỗ trợ hoàn thiện phân hệ tra cứu cho dự án chính của công ty và nghiên cứu nền tảng cho module thực tập cá nhân – đều đạt kết quả tốt, được cán bộ hướng dẫn tại đơn vị ghi nhận.",
        bold_prefix="Đánh giá kết quả tuần 3:"
    )
    add_p(
        doc,
        "Bám sát tiến độ trong Nhật ký thực tập hàng ngày, các nhiệm vụ trọng tâm em sẽ thực hiện trong Tuần 4 bao gồm:",
        bold_prefix="Kế hoạch công tác Tuần 4 (Từ 24/08/2026 đến 28/08/2026):"
    )
    add_bullet(
        doc,
        "Thứ 2 (24/08/2026): Khảo sát và sửa lỗi chuyển báo cáo đang chuyển sai người nhận trong luồng phê duyệt văn bản.",
        "Dự án eForm"
    )
    add_bullet(
        doc,
        "Thứ 3 (25/08/2026): Cấu hình kiểm tra logic kiểm tra tính đúng đắn của biểu mẫu tại tài khoản quản trị hệ thống.",
        "Dự án eForm"
    )
    add_bullet(
        doc,
        "Thứ 4 (26/08/2026): Kiểm tra và hoàn thiện cơ chế xác thực dữ liệu (validate) khi nhập dữ liệu ở các biểu nhập tròn năm.",
        "Dự án eForm"
    )
    add_bullet(
        doc,
        "Thứ 5 (27/08/2026): Nghiên cứu và phát triển chức năng toàn màn hình (Fullscreen) khi hiển thị nội dung biểu mẫu báo cáo.",
        "Dự án eForm"
    )
    add_bullet(
        doc,
        "Thứ 6 (28/08/2026): Rà soát dữ liệu đã chuẩn bị cho module Import Excel, bổ sung các mẫu biểu nhiều tầng, nhiều bảng và các dòng ghi chú phức tạp.",
        "Module Import Excel"
    )
    
    out_path = r"c:\Users\hoang\Downloads\eform_btp\Docs\Tuần 3\BÁO cáo thực tập tuần 3.docx"
    doc.save(out_path)
    print(f"Đã tạo thành công báo cáo thực tập: {out_path}")

if __name__ == "__main__":
    generate_week_3()
