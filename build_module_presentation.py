import os
import sys

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi bảng mã
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

from slide_helper import (
    NAVY_PRIMARY, BLUE_ACCENT, SLATE_DARK, SLATE_MUTED, BG_LIGHT, WHITE,
    CARD_BG, BORDER_COLOR, GREEN_ACCENT, RED_ACCENT, LOGO_HUCE,
    add_slide_transition, create_module_base_slide, add_card, add_image_card
)

def build_module_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # =========================================================================
    # SLIDE 1: TRANG BÌA CHUYÊN ĐỀ
    # =========================================================================
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_transition(s1)

    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid(); bg1.fill.fore_color.rgb = NAVY_PRIMARY; bg1.line.fill.background()

    bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.4), prs.slide_height)
    bar1.fill.solid(); bar1.fill.fore_color.rgb = BLUE_ACCENT; bar1.line.fill.background()

    if os.path.exists(LOGO_HUCE):
        s1.shapes.add_picture(LOGO_HUCE, Inches(11.2), Inches(0.6), width=Inches(1.5))

    tx_uni = s1.shapes.add_textbox(Inches(0.9), Inches(0.6), Inches(9.8), Inches(0.9))
    tf_uni = tx_uni.text_frame
    p_u1 = tf_uni.paragraphs[0]
    p_u1.text = "TRƯỜNG ĐẠI HỌC XÂY DỰNG HÀ NỘI"
    p_u1.font.name = "Arial"; p_u1.font.size = Pt(14); p_u1.font.bold = True
    p_u1.font.color.rgb = RGBColor(147, 197, 253)

    p_u2 = tf_uni.add_paragraph()
    p_u2.text = "KHOA CÔNG NGHỆ THÔNG TIN - BỘ MÔN KHOA HỌC MÁY TÍNH"
    p_u2.font.name = "Arial"; p_u2.font.size = Pt(12); p_u2.font.bold = True
    p_u2.font.color.rgb = RGBColor(203, 213, 225)

    line1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(1.6), Inches(11.5), Inches(0.02))
    line1.fill.solid(); line1.fill.fore_color.rgb = RGBColor(56, 189, 248); line1.line.fill.background()

    tx_title = s1.shapes.add_textbox(Inches(0.9), Inches(1.8), Inches(11.5), Inches(2.4))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True

    p_t1 = tf_title.paragraphs[0]
    p_t1.text = "BÁO CÁO CHUYÊN ĐỀ KỸ THUẬT DỰ ÁN"
    p_t1.font.name = "Arial"; p_t1.font.size = Pt(15); p_t1.font.bold = True
    p_t1.font.color.rgb = RGBColor(56, 189, 248)

    p_t2 = tf_title.add_paragraph()
    p_t2.text = "MODULE IMPORT EXCEL THÔNG MINH ỨNG DỤNG AI & SCHEMA MAPPING"
    p_t2.font.name = "Arial"; p_t2.font.size = Pt(24); p_t2.font.bold = True
    p_t2.font.color.rgb = WHITE

    p_t3 = tf_title.add_paragraph()
    p_t3.text = "Giải pháp trích xuất bảng tính đa cấp, lưới xem trước Handsontable và Vòng lặp Cache tự học cho Hệ thống Quản trị Báo cáo Thống kê điện tử ngành Tư pháp (eForm BTP)"
    p_t3.font.name = "Arial"; p_t3.font.size = Pt(13); p_t3.font.italic = True
    p_t3.font.color.rgb = RGBColor(224, 231, 255)

    info_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(4.5), Inches(11.5), Inches(2.3))
    info_card.fill.solid(); info_card.fill.fore_color.rgb = RGBColor(15, 23, 42)
    info_card.line.color.rgb = RGBColor(51, 65, 85); info_card.line.width = Pt(1)

    tx_c1 = s1.shapes.add_textbox(Inches(1.2), Inches(4.7), Inches(5.3), Inches(1.9))
    tf_c1 = tx_c1.text_frame
    p_i1 = tf_c1.paragraphs[0]
    p_i1.text = "Sinh viên thực hiện: Trần Văn Hoàng"
    p_i1.font.bold = True; p_i1.font.size = Pt(14); p_i1.font.color.rgb = WHITE
    for label, val in [("Mã số sinh viên:", "0034467"), ("Lớp chuyên ngành:", "67CS - Khóa K67"), ("Ngành đào tạo:", "Khoa học máy tính")]:
        p = tf_c1.add_paragraph()
        p.text = f"{label} {val}"
        p.font.size = Pt(13); p.font.color.rgb = RGBColor(203, 213, 225)

    tx_c2 = s1.shapes.add_textbox(Inches(6.8), Inches(4.7), Inches(5.3), Inches(1.9))
    tf_c2 = tx_c2.text_frame
    p_i2 = tf_c2.paragraphs[0]
    p_i2.text = "Cơ quan thực tập: Công ty TNHH Nền tảng chuyển đổi số VN"
    p_i2.font.bold = True; p_i2.font.size = Pt(14); p_i2.font.color.rgb = WHITE
    for label, val in [("Cán bộ hướng dẫn (ĐVTT):", "Đào Đức Văn (Technical Lead - Bkav eGov)"), ("Giảng viên hướng dẫn:", "TS. Hoàng Nam Thắng (Khoa CNTT - HUCE)"), ("Nền tảng ứng dụng:", "eForm BTP (baocaothongke.moj.gov.vn)")]:
        p = tf_c2.add_paragraph()
        p.text = f"{label} {val}"
        p.font.size = Pt(13); p.font.color.rgb = RGBColor(203, 213, 225)

    # =========================================================================
    # SLIDE 2: BỐI CẢNH BÀI TOÁN & THÁCH THỨC BẢNG TÍNH NGÀNH TƯ PHÁP
    # =========================================================================
    s2 = create_module_base_slide(prs, "BỐI CẢNH BÀI TOÁN VÀ THÁCH THỨC BẢNG TÍNH NGÀNH TƯ PHÁP", "1. ĐẶT VẤN ĐỀ", 2)
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "BỐI CẢNH THU THẬP SỐ LIỆU eFORM BTP")
    tx = s2.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    context_pts = [
        ("Hệ thống Báo cáo điện tử eForm BTP:", "Thu thập và tổng hợp số liệu thống kê định kỳ từ 63 Sở Tư pháp, hàng trăm Phòng Tư pháp cấp huyện và hơn 3.300 UBND cấp xã/phường trên toàn quốc."),
        ("Quy mô danh mục biểu mẫu nghiệp vụ:", "Bao gồm 27 mẫu biểu báo cáo thống kê phức tạp (hộ tịch, quốc tịch, công chứng, chứng thực, thi hành án dân sự, trợ giúp pháp lý...)."),
        ("Tập quán nộp báo cáo thực tế:", "Đa phần cán bộ cơ sở tổng hợp số liệu trên các file Excel cục bộ rồi tải lên hệ thống. Tệp Excel được trình bày thủ công theo thói quen in ấn văn bản hành chính."),
        ("Nút thắt cổ chai nhập liệu:", "Nhập tay từng ô trên giao diện web gây tốn hàng nghìn giờ công lao động mỗi kỳ báo cáo, dễ sai sót và gây quá tải hệ thống trong các ngày chốt sổ.")
    ]
    for h, b in context_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "4 THÁCH THỨC KỸ THUẬT ĐẶC THÙ")
    tx2 = s2.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    challenges_pts = [
        ("Tiêu đề đa tầng lồng nhau sâu (4 - 6 cấp):", "Biểu mẫu hành chính thường có tiêu đề phân cấp nhiều tầng (Nhóm việc -> Việc có điều kiện -> Đã giải quyết xong)."),
        ("Khối ô gộp (Merged Cells) dày đặc:", "Điển hình như Biểu 21a có tới 78 khối ô gộp phức tạp theo cả chiều ngang và dọc, làm xô lệch toàn bộ chỉ mục cột nếu đọc tuần tự."),
        ("Vùng dữ liệu nhiễu chân trang (Footers):", "Các dòng căn cứ pháp lý, ghi chú động, danh sách nơi nhận và chữ ký lãnh đạo nằm ngay sát đáy bảng, dễ bị đọc nhầm thành dữ liệu."),
        ("Sự thất bại của các bộ parser truyền thống:", "Các thư viện đọc bảng thông thường (EPPlus thuần, pandas) không thể hiểu ngữ nghĩa phân cấp, dẫn đến việc ánh xạ sai cột hoặc phát sinh ngoại lệ hàng loạt.")
    ]
    for h, b in challenges_pts:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = RED_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 3: NGUYÊN TẮC THIẾT KẾ & PHÂN ĐỊNH RANH GIỚI TRÁCH NHIỆM
    # =========================================================================
    s3 = create_module_base_slide(prs, "NGUYÊN TẮC THIẾT KẾ VÀ PHÂN ĐỊNH RANH GIỚI TRÁCH NHIỆM", "2. THIẾT KẾ KIẾN TRÚC", 3)
    principles = [
        ("1. AI LÀ TRỢ LÝ NHẬN DIỆN CẤU TRÚC THÔ",
         "Mô hình AI chỉ chịu trách nhiệm bóc tách bố cục hình học, nhận diện vùng Header Mask, Value Mask và phân cấp chỉ tiêu. AI tuyệt đối KHÔNG có quyền can thiệp hay ghi trực tiếp vào Cơ sở dữ liệu nghiệp vụ của Bộ Tư pháp.",
         Inches(0.8), Inches(1.5), Inches(5.7), Inches(2.5)),
        ("2. BACKEND C# LÀ CHỐT CHẶN NGHIỆP VỤ AN TOÀN",
         "Toàn bộ dữ liệu sau khi AI trích xuất phải được chuyển về Backend C# (.NET Framework 4.8 / Web API). Tại đây, hệ thống thực hiện kiểm duyệt kiểu dữ liệu, thẩm định quyền hạn tài khoản, kiểm tra xung đột khóa sổ và quản lý Transaction nguyên tử.",
         Inches(6.8), Inches(1.5), Inches(5.7), Inches(2.5)),
        ("3. TÍNH ĐỘC LẬP VÀ KHÔNG XÂM LẤN (NON-INTRUSIVE)",
         "Module được thiết kế phân tầng hoàn toàn độc lập (Microservice kiến trúc mở). Tuyệt đối không thay đổi cấu trúc bảng cơ sở dữ liệu lõi của eForm BTP cũ; tích hợp thông qua API và dịch vụ lưu trữ an toàn, đảm bảo tính kế thừa 100%.",
         Inches(0.8), Inches(4.3), Inches(5.7), Inches(2.5)),
        ("4. QUYỀN KIỂM SOÁT TỐI HẬU THUỘC VỀ CON NGƯỜI",
         "Áp dụng triết lý Human-in-the-loop: Cán bộ chuyên môn luôn được xem trước toàn bộ kết quả bóc tách trên lưới bảng tính Handsontable đa cấp, được quyền chỉnh sửa trực tiếp từng ô và xác nhận qua Modal trước khi bấm lưu chính thức.",
         Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.5))
    ]
    for p_title, p_content, left, top, w, h in principles:
        add_card(s3, left, top, w, h, p_title)
        tx = s3.shapes.add_textbox(left + Inches(0.2), top + Inches(0.55), w - Inches(0.4), h - Inches(0.65))
        p = tx.text_frame.paragraphs[0]; p.text = p_content
        p.font.size = Pt(11.5); p.font.color.rgb = SLATE_DARK; p.alignment = PP_ALIGN.JUSTIFY

    # =========================================================================
    # SLIDE 4: KIẾN TRÚC HỆ THỐNG TỔNG THỂ (SYSTEM ARCHITECTURE)
    # =========================================================================
    s4 = create_module_base_slide(prs, "KIẾN TRÚC HỆ THỐNG TỔNG THỂ (SYSTEM ARCHITECTURE)", "2. THIẾT KẾ KIẾN TRÚC", 4)
    # Cột trái: Ảnh kiến trúc
    arch_img = r"Docs\Tuần 2\So_do_kien_truc_Module_Import_Excel.png"
    add_image_card(s4, Inches(0.8), Inches(1.5), Inches(6.0), Inches(5.2), arch_img,
                   "SƠ ĐỒ KIẾN TRÚC PHÂN TẦNG CLEAN ARCHITECTURE",
                   "Kiến trúc phân tầng tách biệt giữa Giao diện, Backend C#, Dịch vụ AI và CSDL eForm")

    # Cột phải: Thuyết minh 4 tầng
    add_card(s4, Inches(7.0), Inches(1.5), Inches(5.5), Inches(5.2), "PHÂN TÍCH 4 TẦNG KIẾN TRÚC")
    tx = s4.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.1), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    tiers = [
        ("Tầng 1: Client Application (Trình duyệt cán bộ)",
         "Giao diện tải tệp AJAX kéo thả, lưới xem trước dữ liệu Handsontable đa cấp, bộ đệm LocalStorage lưu trữ ánh xạ tức thời (< 5ms)."),
        ("Tầng 2: Backend API Gateway (ASP.NET MVC 5 / C#)",
         "Xây dựng ImportService, tiếp nhận Multipart file, kiểm tra tính toàn vẹn (Magic Bytes PK), điều phối giao tiếp AI và xử lý lưu DB an toàn qua Entity Framework 6."),
        ("Tầng 3: AI Microservice Engine (Python FastAPI)",
         "Đóng gói độc lập trên máy chủ; bóc tách ma trận hình học bằng openpyxl; chạy mô hình Compact U-Net; thực hiện thuật toán footer-trim và xuất JSON Schema 2.0."),
        ("Tầng 4: Data Persistence & Distributed Cache",
         "Cơ sở dữ liệu eForm Datamart (MySQL/LocalDB), lưu DocumentContent và FactData; bộ nhớ đệm phân tán Redis Cache tăng tốc truy xuất báo cáo.")
    ]
    for t_name, t_desc in tiers:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + t_name; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + t_desc; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 5: SƠ ĐỒ LUỒNG DỮ LIỆU TOÀN TRÌNH (DATA FLOW PIPELINE)
    # =========================================================================
    s5 = create_module_base_slide(prs, "SƠ ĐỒ LUỒNG DỮ LIỆU TOÀN TRÌNH (DATA FLOW PIPELINE)", "2. THIẾT KẾ KIẾN TRÚC", 5)
    # Cột trái: Ảnh luồng dữ liệu
    df_img = r"Docs\Tuần 2\So_do_luong_du_lieu_Data_Flow.png"
    add_image_card(s5, Inches(0.8), Inches(1.5), Inches(6.0), Inches(5.2), df_img,
                   "SƠ ĐỒ LUỒNG DỮ LIỆU TOÀN TRÌNH TỪ FILE EXCEL ĐẾN CSDL",
                   "Quy trình xử lý khép kín 6 bước: Upload -> Geometry -> AI -> Schema -> Preview -> Persistence")

    # Cột phải: Thuyết minh 6 bước pipeline
    add_card(s5, Inches(7.0), Inches(1.5), Inches(5.5), Inches(5.2), "QUY TRÌNH 6 BƯỚC KHÉP KÍN")
    tx = s5.shapes.add_textbox(Inches(7.2), Inches(2.1), Inches(5.1), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    steps = [
        ("Bước 1: Tiếp nhận tệp & Kiểm tra phòng vệ", "Client upload file qua AJAX; Backend kiểm tra dung lượng (<50MB) và Magic Bytes ngăn chặn file giả mạo."),
        ("Bước 2: Bóc tách ma trận hình học (Grid Geometry)", "AI Service đọc workbook trực tiếp, trích xuất cấu trúc ô gộp và ma trận bảng tính không cần render ảnh."),
        ("Bước 3: Nhận diện phân vùng & Cắt tỉa Footer-Trim", "Mô hình Compact U-Net phân đoạn Header/Value; thuật toán footer-trim loại bỏ hoàn toàn chữ ký và ghi chú rác."),
        ("Bước 4: Chuẩn hóa phân cấp & Phát hành JSON 2.0", "Xây dựng cây chỉ tiêu phân cấp (Cấp 0 -> Cấp 3), tạo hợp đồng JSON Schema 2.0 chuẩn chỉ gửi về Client."),
        ("Bước 5: Render Handsontable & Chỉnh sửa trực tiếp", "Tái hiện chính xác 6 tầng header, 78 ô gộp; cán bộ sửa ô tại chỗ với cảnh báo viền màu hổ phách."),
        ("Bước 6: Kích hoạt Cache tự học & Lưu CSDL an toàn", "Lưu quy tắc sửa vào Cache 2 tầng; Modal xác nhận gửi dữ liệu sang Backend C# thực hiện lưu trữ nguyên tử.")
    ]
    for s_name, s_desc in steps:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = s_name; p1.font.bold = True; p1.font.size = Pt(11); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + s_desc; p2.font.size = Pt(10.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 6: BÓC TÁCH HÌNH HỌC & CHỐNG RÒ RỈ DỮ LIỆU (LAYOUT FINGERPRINT)
    # =========================================================================
    s6 = create_module_base_slide(prs, "BÓC TÁCH HÌNH HỌC VÀ CHỐNG RÒ RỈ DỮ LIỆU (LAYOUT FINGERPRINT)", "3. PHÁT TRIỂN AI & XỬ LÝ DỮ LIỆU", 6)
    diag_img = r"Docs\Tuần 4\diagrams\01_QUY_TRINH_NHAN_DIEN_VA_TRICH_XUAT.png"
    add_image_card(s6, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), diag_img,
                   "QUY TRÌNH NHẬN DIỆN VÀ TRÍCH XUẤT CẤU TRÚC",
                   "Thuật toán bóc tách ma trận hình học kết hợp trích xuất Layout Fingerprint")

    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "PHƯƠNG PHÁP CHỐNG DATA LEAKAGE")
    tx = s6.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    leak_pts = [
        ("Bóc tách ma trận hình học không phụ thuộc OCR:",
         "Thay vì chuyển đổi bảng sang hình ảnh rồi chạy OCR tốn kém tài nguyên và dễ sai số, module trích xuất trực tiếp tọa độ (row, col), trạng thái ô gộp và kiểu dữ liệu bằng openpyxl; tốc độ tăng gấp 15 lần."),
        ("Khái niệm Vân tay bố cục (Layout Fingerprint):",
         "Mỗi biểu mẫu được mã hóa thành một chuỗi đặc trưng hình học đại diện (số lượng cột, tỷ lệ ô gộp tại 10 dòng đầu, phân bố hàng rỗng và từ khóa tiêu đề cốt lõi)."),
        ("Nguy cơ rò rỉ dữ liệu (Data Leakage) trong AI:",
         "Nếu chia dữ liệu ngẫu nhiên theo từng file, các file có cùng một mẫu biểu sẽ xuất hiện ở cả tập Train và Test, khiến mô hình 'học vẹt' và cho độ chính xác ảo."),
        ("Chiến lược chia cụm theo họ bố cục (Cluster Splitting):",
         "Gom toàn bộ các file cùng một Layout Fingerprint vào một cụm duy nhất. Mỗi cụm chỉ nằm độc quyền trong một tập: Train (70%), Validation (15%) hoặc Test (15%), đảm bảo tính khách quan và khả năng tổng quát hóa.")
    ]
    for h, b in leak_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 7: MÔ HÌNH HỌC SÂU COMPACT U-NET & THUẬT TOÁN FOOTER-TRIM
    # =========================================================================
    s7 = create_module_base_slide(prs, "MÔ HÌNH HỌC SÂU COMPACT U-NET VÀ THUẬT TOÁN FOOTER-TRIM", "3. PHÁT TRIỂN AI & XỬ LÝ DỮ LIỆU", 7)
    train_img = r"Docs\Tuần 5\evidence\training_curves_actual.png"
    add_image_card(s7, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), train_img,
                   "ĐỒ THỊ HUẤN LUYỆN THỰC TẾ (TRAINING LOSS & ACCURACY)",
                   "Quá trình huấn luyện Compact U-Net qua 14 epoch với cơ chế Early Stopping trên PyTorch")

    add_card(s7, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "THÔNG SỐ KỸ THUẬT VÀ THUẬT TOÁN CẮT TỈA")
    tx = s7.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    unet_pts = [
        ("Kiến trúc mạng Compact U-Net 2D (PyTorch):",
         "Mạng nơ-ron phân đoạn ảnh ma trận bảng tính với cấu trúc Encoder - Decoder thu gọn; tối ưu hóa đặc biệt để chạy mượt mà trên CPU thông thường mà không cần GPU đắt đỏ."),
        ("Quy mô tham số siêu nhẹ & Tốc độ ấn tượng:",
         "Tổng số tham số: 379.107 tham số; dung lượng file trọng số mô hình chỉ 1,48 MB; thời gian suy luận trên một workbook < 250ms."),
        ("Kết quả đánh giá trên tập kiểm thử độc lập:",
         "Huấn luyện 14 epoch kích hoạt Early Stopping khi Validation Loss chạm đáy; F1-score vùng Header đạt 94,82%; F1-score vùng Value đạt 96,15%."),
        ("Thuật toán cắt tỉa chân trang (Footer-Trim Algorithm):",
         "Quét ngược từ đáy bảng lên, nhận diện mật độ các từ khóa hành chính đặc thù ('Nơi nhận:', 'Ghi chú:', 'Thủ trưởng đơn vị ký tên'); tự động cắt tỉa toàn bộ vùng rác, khôi phục đường biên dưới của bảng sạch 100%.")
    ]
    for h, b in unet_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 8: CHUẨN HÓA CÂY PHÂN CẤP CHỈ TIÊU & HỢP ĐỒNG JSON SCHEMA 2.0
    # =========================================================================
    s8 = create_module_base_slide(prs, "CHUẨN HÓA CÂY PHÂN CẤP CHỈ TIÊU VÀ HỢP ĐỒNG JSON SCHEMA 2.0", "3. PHÁT TRIỂN AI & XỬ LÝ DỮ LIỆU", 8)
    add_card(s8, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "QUY TẮC PHÂN CẤP CÂY CHỈ TIÊU (HIERARCHY)")
    tx = s8.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    tree_pts = [
        ("Cơ chế phân cấp chỉ mục tự động:",
         "Phân tích cú pháp chuỗi văn bản cột đầu tiên của bảng tính để xác định cấp bậc quan hệ cha - con giữa các dòng số liệu."),
        ("Quy chuẩn 4 cấp bậc chỉ tiêu hành chính:",
         "• Cấp 0 (Gốc): Dòng 'Tổng số' hoặc chỉ tiêu toàn quốc.\n"
         "• Cấp 1: Ký hiệu số La Mã (I, II, III, IV...) - Lĩnh vực công tác lớn.\n"
         "• Cấp 2: Ký hiệu số Ả Rập (1, 2, 3...) - Phân nhóm nghiệp vụ chi tiết.\n"
         "• Cấp 3: Ký hiệu số thập phân / chữ cái (1.1, 1.2, a, b...) - Chỉ tiêu cơ sở."),
        ("Kết quả kiểm chứng trên dữ liệu Bộ Tư pháp:",
         "Thực hiện đối soát trên 4.656 ô dữ liệu thực tế thuộc các biểu mẫu phức tạp (Biểu 04c, 11b, 21a), độ chính xác phân cấp đạt 100% không xảy ra đứt gãy nhánh cây.")
    ]
    for h, b in tree_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "CẤU TRÚC HỢP ĐỒNG JSON SCHEMA 2.0 (FASTAPI)")
    tx2 = s8.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    json_spec = [
        ("metadata", "{\n  workbookName: 'Bieu_21a_THADS.xlsx',\n  fingerprint: 'fp_a9b8c7d6',\n  totalRows: 142, totalCols: 38\n}"),
        ("mergedCells", "[\n  { row: 0, col: 2, rowspan: 2, colspan: 3 },\n  { row: 2, col: 5, rowspan: 4, colspan: 1 }\n] // 78 ô gộp"),
        ("headerPath", "[\n  ['Thi hành án', 'Có điều kiện', 'Đã xong số tiền'],\n  ['Hộ tịch', 'Đăng ký khai sinh', 'Đúng hạn']\n]"),
        ("hierarchyPath", "['Tổng số', 'I. Việc có điều kiện', '1. Đã thi hành xong']")
    ]
    p_lead = tf2.paragraphs[0]
    p_lead.text = "Đặc tả Hợp đồng dữ liệu JSON chuẩn trao đổi giữa FastAPI và C#:"
    p_lead.font.size = Pt(11.5); p_lead.font.bold = True; p_lead.font.color.rgb = BLUE_ACCENT
    for field, code_snip in json_spec:
        p_f = tf2.add_paragraph()
        p_f.text = f"• Khóa '{field}':"
        p_f.font.bold = True; p_f.font.size = Pt(11); p_f.font.color.rgb = NAVY_PRIMARY
        p_c = tf2.add_paragraph()
        p_c.text = code_snip
        p_c.font.name = "Consolas"; p_c.font.size = Pt(10); p_c.font.color.rgb = RGBColor(15, 23, 42)

    # =========================================================================
    # SLIDE 9: GIAO DIỆN XEM TRƯỚC ĐA CẤP HANDSONTABLE GRID
    # =========================================================================
    s9 = create_module_base_slide(prs, "GIAO DIỆN XEM TRƯỚC ĐA CẤP HANDSONTABLE GRID", "4. GIAO DIỆN & TƯƠNG TÁC", 9)
    ht_img = r"Docs\Tuần 8\evidence\01_UI_PREVIEW_HANDSONTABLE_DA_CAP.png"
    add_image_card(s9, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), ht_img,
                   "GIAO DIỆN LƯỚI XEM TRƯỚC DỮ LIỆU ĐA CẤP",
                   "Tái hiện trung thực 6 tầng tiêu đề, 78 khối ô gộp và tính năng sửa ô trực tiếp")

    add_card(s9, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "CÔNG THÁI HỌC VÀ TRẢI NGHIỆM NGƯỜI DÙNG")
    tx = s9.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    ht_pts = [
        ("Tái hiện 100% hình thái Excel gốc:",
         "Tích hợp Handsontable Engine giúp hiển thị chuẩn xác từng ô gộp (mergeCells), giữ nguyên cấu trúc đa tầng lồng nhau mà không bị xô lệch vị trí cột."),
        ("Cố định tiêu đề & Cuộn mượt mà hai chiều:",
         "Khóa cứng 6 hàng tiêu đề trên cùng (fixedRowsTop: 6). Khi cán bộ cuộn chuột qua hàng trăm dòng số liệu, tiêu đề vẫn được ghim chắc chắn, không bị mất ngữ cảnh."),
        ("Chỉnh sửa trực tiếp trên ô (Inline Cell Editing):",
         "Cho phép người dùng nhấp đúp vào ô bất kỳ để chỉnh sửa giá trị. Hook afterChange tự động bắt tọa độ ô, đối chiếu giá trị cũ/mới và hiển thị viền cảnh báo màu cam hổ phách."),
        ("Thao tác phím tắt thân thiện chuẩn Excel:",
         "Hỗ trợ đầy đủ các phím điều hướng (Mũi tên, Tab, Enter), thao tác sao chép - dán khối ô (Ctrl+C / Ctrl+V), giúp cán bộ làm việc với tốc độ cao nhất.")
    ]
    for h, b in ht_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 10: CƠ CHẾ VÒNG LẶP CACHE TỰ HỌC (SELF-LEARNING CACHE LOOP)
    # =========================================================================
    s10 = create_module_base_slide(prs, "CƠ CHẾ VÒNG LẶP CACHE TỰ HỌC (SELF-LEARNING CACHE LOOP)", "4. GIAO DIỆN & TƯƠNG TÁC", 10)
    cache_img = r"Docs\Tuần 9\diagrams\01_LUONG_CACHE_TU_HOC_GIAM_GOI_AI.png"
    add_image_card(s10, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), cache_img,
                   "SƠ ĐỒ VÒNG LẶP CACHE TỰ HỌC 2 TẦNG",
                   "Cơ chế lưu trữ đệm Hybrid (Client LocalStorage + Server) giảm tải >90% gọi AI")

    add_card(s10, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "HIỆU QUẢ TỐI ƯU HÓA TÀI NGUYÊN")
    tx = s10.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    cache_details = [
        ("Vấn đề lãng phí tài nguyên suy luận AI:",
         "Nếu mỗi lần người dùng nạp file cùng một mẫu biểu đều phải kích hoạt toàn bộ tiến trình phân tích AI thì sẽ gây quá tải CPU máy chủ và tạo độ trễ chờ đợi không đáng có."),
        ("Cơ chế lưu trữ đệm 2 tầng (Hybrid Cache):",
         "• Tầng 1 (Client): Ghi nhận ngay quy tắc sửa đổi vào LocalStorage (< 5ms) theo khóa fingerprint của bảng tính.\n"
         "• Tầng 2 (Server): Đồng bộ bản sửa lên ASP.NET Backend qua API POST /api/import/feedback, lưu vào ConcurrentDictionary an toàn đa luồng."),
        ("Tự động áp dụng quy tắc đã học (Auto-Apply):",
         "Khi tải lại file có cùng Layout Fingerprint, hệ thống tự động kiểm tra cache; nếu tìm thấy quy tắc cũ, tự động điền giá trị sửa và hiển thị Banner màu xanh lá thông báo."),
        ("Giảm tải trên 90% tần suất gọi mô hình AI:",
         "Tốc độ xử lý cho các lần nạp tiếp theo giảm xuống dưới 10ms, tiết kiệm tối đa chi phí hạ tầng máy chủ cho đơn vị vận hành.")
    ]
    for h, b in cache_details:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 11: KIẾN TRÚC PHÒNG VỆ ĐA TẦNG & API LƯU TRỮ AN TOÀN
    # =========================================================================
    s11 = create_module_base_slide(prs, "KIẾN TRÚC PHÒNG VỆ ĐA TẦNG VÀ API LƯU TRỮ AN TOÀN", "5. BẢO MẬT & KIỂM THỬ", 11)
    err_img = r"Docs\Tuần 10\diagrams\01_LUONG_XU_LY_NGOAI_LE_VA_END_TO_END.png"
    add_image_card(s11, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), err_img,
                   "SƠ ĐỒ XỬ LÝ NGOẠI LỆ VÀ LUỒNG END-TO-END",
                   "Kiến trúc phòng vệ 4 lớp kiểm soát lỗi chặt chẽ từ Client, API đến Cơ sở dữ liệu")

    add_card(s11, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "4 LỚP CHỐT CHẶN BẢO VỆ CSDL")
    tx = s11.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    guards = [
        ("Lớp 1: Client Input Guard (Giao diện người dùng):",
         "Bắt lỗi tức thì các file rỗng 0 byte, file vượt quá dung lượng cho phép (>50MB), file sai phần mở rộng; kích hoạt Toast thông báo màu đỏ, ngăn không gửi yêu cầu rác lên server."),
        ("Lớp 2: Format & Magic Bytes Guard (Backend C#):",
         "Đọc chữ ký nhị phân đầu file (PK Header 0x50 0x4B); chặn đứng các trường hợp cố tình đổi đuôi file .exe/.txt thành .xlsx; bắt ngoại lệ hỏng OpenXML trước khi gọi sang AI."),
        ("Lớp 3: Two-Step Confirmation Modal (Xác nhận hai bước):",
         "Trước khi lưu, hệ thống mở hộp thoại tổng hợp toàn bộ số ô đã chỉnh sửa, yêu cầu người dùng xác nhận rõ ràng; loại bỏ hoàn toàn nguy cơ bấm nhầm làm sai lệch số liệu."),
        ("Lớp 4: Atomic Transaction Persistence (Giao dịch nguyên tử):",
         "Backend C# mở một Transaction duy nhất khi ghi vào CSDL; nếu xảy ra bất kỳ lỗi ràng buộc dữ liệu nào, toàn bộ giao dịch được Rollback an toàn, bảo vệ nguyên vẹn hệ thống eForm.")
    ]
    for h, b in guards:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 12: MINH CHỨNG THỰC NGHIỆM BẮT NGOẠI LỆ & LƯU TRỮ THÀNH CÔNG
    # =========================================================================
    s12 = create_module_base_slide(prs, "MINH CHỨNG THỰC NGHIỆM BẮT NGOẠI LỆ VÀ LƯU TRỮ THÀNH CÔNG", "5. BẢO MẬT & KIỂM THỬ", 12)
    img_err = r"Docs\Tuần 10\evidence\01_UI_BAT_LOI_FILE_0_BYTE.png"
    add_image_card(s12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), img_err,
                   "TEST CASE 1: BẮT LỖI TỆP RỖNG 0 BYTE VÀ ĐỊNH DẠNG HỎNG",
                   "Giao diện kích hoạt cảnh báo đỏ chuẩn công thái học, chặn đứng tệp hỏng tại Client")

    img_ok = r"Docs\Tuần 10\evidence\03_UI_LUU_BAO_CAO_THANH_CONG.png"
    add_image_card(s12, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), img_ok,
                   "TEST CASE 2: XÁC NHẬN VÀ LƯU BÁO CÁO THÀNH CÔNG VÀO CSDL",
                   "Banner xanh lá thông báo lưu thành công, dữ liệu được ghi nhận nguyên vẹn vào CSDL")

    # =========================================================================
    # SLIDE 13: KẾT QUẢ THỰC NGHIỆM & KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN
    # =========================================================================
    s13 = create_module_base_slide(prs, "KẾT QUẢ THỰC NGHIỆM VÀ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN", "5. BẢO MẬT & KIỂM THỬ", 13)
    tbl_shape = s13.shapes.add_table(4, 4, Inches(0.8), Inches(1.5), Inches(11.73), Inches(2.7))
    table = tbl_shape.table
    widths = [Inches(3.2), Inches(3.8), Inches(2.5), Inches(2.23)]
    for i, w in enumerate(widths): table.columns[i].width = w

    test_headers = ["Bộ kiểm thử tự động (Test Suite)", "Phạm vi chức năng kiểm thử", "Số ca kiểm thử", "Tỷ lệ vượt qua (Pass Rate)"]
    for j, h in enumerate(test_headers):
        cell = table.cell(0, j); cell.text = h; cell.fill.solid(); cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]; p.font.bold = True; p.font.size = Pt(12); p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    test_results = [
        ("Bộ kiểm thử Giao diện (UI Test Suite)", "Kéo thả upload, cuộn bảng 2 chiều, sửa ô trực tiếp, phím tắt, modal xác nhận, banner trạng thái", "16 Test Cases", "16 / 16 PASS (100%)"),
        ("Bộ kiểm thử Backend C# (Backend Suite)", "Phân tích OpenXML, thẩm định schema JSON 2.0, đồng bộ feedback cache, kiểm soát giao dịch DB", "15 Test Cases", "15 / 15 PASS (100%)"),
        ("Bộ kiểm thử Toàn trình (End-to-End Suite)", "Luồng khép kín từ file thô đến CSDL trên các biểu mẫu thật Biểu 01 đến Biểu 21a Bộ Tư pháp", "12 Test Cases", "12 / 12 PASS (100%)")
    ]
    for i, row in enumerate(test_results):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j); cell.text = val; cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]; p.font.size = Pt(11); p.font.color.rgb = SLATE_DARK
            if j == 0: p.font.bold = True
            if j == 2: p.alignment = PP_ALIGN.CENTER
            if j == 3: p.font.bold = True; p.alignment = PP_ALIGN.CENTER; p.font.color.rgb = GREEN_ACCENT

    # Thẻ tóm tắt các chỉ số hiệu năng
    add_card(s13, Inches(0.8), Inches(4.5), Inches(11.73), Inches(2.3), "CÁC CHỈ SỐ ĐO LƯỜNG HIỆU NĂNG HỆ THỐNG THỰC TẾ")
    tx_perf = s13.shapes.add_textbox(Inches(1.0), Inches(5.0), Inches(11.3), Inches(1.6))
    tf_perf = tx_perf.text_frame; tf_perf.word_wrap = True
    perf_items = [
        ("Thời gian phản hồi trích xuất trung bình:", "Từ 0,8 đến 1,2 giây đối với file bảng tính phức tạp quy mô 500 dòng x 40 cột (giảm 95% thời gian so với nhập tay)."),
        ("Độ chính xác nhận diện phân vùng cấu trúc:", "Đạt 98,6% trên toàn bộ tập kiểm thử độc lập (Test Set) gồm các biểu mẫu thống kê phức tạp nhất của ngành Tư pháp."),
        ("Mức độ tiêu thụ tài nguyên máy chủ:", "Chạy ổn định trên CPU tiêu chuẩn, tiêu tốn dưới 150MB RAM, không yêu cầu trang bị GPU chuyên dụng đắt đỏ."),
        ("Tính sẵn sàng và độ tin cậy:", "100% các ca kiểm thử hồi quy đều thành công; cơ chế Cache tự học giúp các lần nạp sau phản hồi gần như tức thì (< 10ms).")
    ]
    for h, b in perf_items:
        p = tf_perf.add_paragraph() if tf_perf.paragraphs[0].text else tf_perf.paragraphs[0]
        p.text = "• " + h + " " + b
        p.font.size = Pt(11.5); p.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 14: ĐÁNH GIÁ NGHIỆM THU TỪ MENTOR & NHÓM eGOV SOLUTIONS
    # =========================================================================
    s14 = create_module_base_slide(prs, "ĐÁNH GIÁ NGHIỆM THU TỪ MENTOR VÀ NHÓM eGOV SOLUTIONS", "6. ĐÁNH GIÁ & ĐỊNH HƯỚNG", 14)
    sc_img = r"Docs\Tuần 11\05_showcase_module_ai_import_preview_handsontable.png"
    add_image_card(s14, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2), sc_img,
                   "BUỔI BÁO CÁO SHOWCASE VỚI MENTOR ĐÀO ĐỨC VĂN (16/10/2026)",
                   "Trình diễn trực tiếp toàn bộ luồng chức năng Module Import Excel AI trên hệ thống thật")

    add_card(s14, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "Ý KIẾN NGHIỆM THU CỦA ĐƠN VỊ THỰC TẬP")
    tx = s14.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    mentor_feedback = [
        ("Đánh giá của Cán bộ hướng dẫn: Anh Đào Đức Văn (Technical Lead)",
         "Sinh viên Trần Văn Hoàng đã hoàn thành xuất sắc đề tài được giao. Module có tư duy thiết kế rất tốt, biết phân định rõ ràng vai trò của AI và Backend, xử lý bài toán ô gộp và phân cấp tiêu đề sâu cực kỳ thuyết phục."),
        ("Giá trị ứng dụng thực tiễn cao:",
         "Giải quyết đúng vào bài toán nhức nhối nhất trong thu thập số liệu hành chính. Giúp giảm tải áp lực cho cán bộ tổng hợp tại các Sở Tư pháp và Cục chuyên ngành."),
        ("Chất lượng mã nguồn và tài liệu:",
         "Mã nguồn được cấu trúc sạch sẽ theo Clean Architecture, có đầy đủ tài liệu Swagger API, các kịch bản kiểm thử tự động Playwright bài bản và báo cáo tiến độ chỉn chu."),
        ("Kết luận nghiệm thu:", "ĐẠT LOẠI XUẤT SẮC - Đủ điều kiện triển khai thử nghiệm thực tế và phát triển tiếp thành Đồ án tốt nghiệp đại học.")
    ]
    for h, b in mentor_feedback:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(11.5)
        p1.font.color.rgb = GREEN_ACCENT if "Kết luận" in h else NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK
        if "XUẤT SẮC" in b: p2.font.bold = True; p2.font.color.rgb = GREEN_ACCENT

    # =========================================================================
    # SLIDE 15: KHẢ NĂNG MỞ RỘNG & ĐỊNH HƯỚNG PHÁT TRIỂN ĐỒ ÁN TỐT NGHIỆP
    # =========================================================================
    s15 = create_module_base_slide(prs, "KHẢ NĂNG MỞ RỘNG VÀ ĐỊNH HƯỚNG PHÁT TRIỂN ĐỒ ÁN TỐT NGHIỆP", "6. ĐÁNH GIÁ & ĐỊNH HƯỚNG", 15)
    add_card(s15, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "TIỀM NĂNG MỞ RỘNG CHỨC NĂNG HỆ THỐNG")
    tx = s15.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    expansion_pts = [
        ("1. Tích hợp Module OCR nhận diện tài liệu Scan / Ảnh:",
         "Mở rộng khả năng tiếp nhận sang các tệp PDF scan hoặc ảnh chụp biểu mẫu giấy tờ từ cơ sở bằng cách kết hợp thêm mô hình OCR tiền xử lý (như PaddleOCR hoặc TrOCR)."),
        ("2. Tự động đối soát công thức toán học chéo (Cross-check Validation):",
         "Phát triển tính năng tự động kiểm tra tính đúng đắn logic của số liệu ngay trên lưới xem trước (ví dụ: Tổng số = Cột A + Cột B, Số phát sinh <= Số tồn đầu kỳ)."),
        ("3. Đóng gói Container hóa (Docker & Kubernetes):",
         "Đóng gói toàn bộ dịch vụ AI FastAPI và Backend thành các Docker Container chuẩn hóa, sẵn sàng triển khai trên cụm máy chủ đám mây của Trung tâm Dữ liệu Bộ Tư pháp.")
    ]
    for h, b in expansion_pts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s15, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "KẾ HOẠCH PHÁT TRIỂN ĐỒ ÁN TỐT NGHIỆP TẠI HUCE")
    tx2 = s15.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    thesis_plan = [
        ("Đăng ký đề tài Đồ án tốt nghiệp chính thức:",
         "Đề xuất hướng nghiên cứu: 'Nghiên cứu ứng dụng Học sâu và Kiến trúc vi dịch vụ trong trích xuất, ánh xạ lược đồ bảng tính bán cấu trúc phục vụ Chuyển đổi số Chính phủ'."),
        ("Dưới sự hướng dẫn học thuật của Giảng viên:",
         "Kính mong tiếp tục nhận được sự định hướng khoa học từ TS. Hoàng Nam Thắng (Khoa CNTT - HUCE) để đào sâu thêm cơ sở lý thuyết về mạng đồ thị (Graph Neural Networks) trong biểu diễn cấu trúc bảng."),
        ("Phối hợp với doanh nghiệp thực nghiệm:",
         "Tiếp tục phối hợp chặt chẽ với Cán bộ hướng dẫn Đào Đức Văn và nhóm eGov để thử nghiệm trên tập dữ liệu thực tế lớn hơn trong các kỳ báo cáo năm của Bộ Tư pháp.")
    ]
    for h, b in thesis_plan:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 16: PHIÊN HỎI ĐÁP & KẾT THÚC (Q&A)
    # =========================================================================
    s16 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_transition(s16)

    bg16 = s16.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg16.fill.solid(); bg16.fill.fore_color.rgb = NAVY_PRIMARY; bg16.line.fill.background()

    if os.path.exists(LOGO_HUCE):
        s16.shapes.add_picture(LOGO_HUCE, Inches(5.9), Inches(1.2), width=Inches(1.5))

    tx_end = s16.shapes.add_textbox(Inches(1.0), Inches(2.9), Inches(11.33), Inches(3.0))
    tf_end = tx_end.text_frame
    p_e1 = tf_end.paragraphs[0]
    p_e1.text = "TRÂN TRỌNG CẢM ƠN QUÝ THẦY CÔ VÀ HỘI ĐỒNG!"
    p_e1.font.name = "Arial"; p_e1.font.size = Pt(26); p_e1.font.bold = True
    p_e1.font.color.rgb = WHITE; p_e1.alignment = PP_ALIGN.CENTER

    p_e2 = tf_end.add_paragraph()
    p_e2.text = "BÁO CÁO CHUYÊN ĐỀ KỸ THUẬT: MODULE IMPORT EXCEL THÔNG MINH ỨNG DỤNG AI (eFORM BTP)"
    p_e2.font.name = "Arial"; p_e2.font.size = Pt(15); p_e2.font.bold = True
    p_e2.font.color.rgb = RGBColor(186, 230, 253); p_e2.alignment = PP_ALIGN.CENTER

    p_e3 = tf_end.add_paragraph()
    p_e3.text = "\nEM XIN LẮNG NGHE VÀ TRẢ LỜI CÁC CÂU HỎI CHUYÊN MÔN TỪ HỘI ĐỒNG (Q&A)"
    p_e3.font.name = "Arial"; p_e3.font.size = Pt(16); p_e3.font.bold = True
    p_e3.font.color.rgb = RGBColor(56, 189, 248); p_e3.alignment = PP_ALIGN.CENTER

    out_file2 = "Module Import Excel Thong Minh - eForm BTP.pptx"
    prs.save(out_file2)
    print(f"Saved {out_file2} successfully with {len(prs.slides)} slides!")

if __name__ == '__main__':
    build_module_presentation()
