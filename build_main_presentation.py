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
    add_slide_transition, create_base_slide, add_card
)

def build_presentation():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # =========================================================================
    # SLIDE 1: TRANG BÌA
    # =========================================================================
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_transition(s1)

    # Nền Navy sang trọng
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY_PRIMARY
    bg1.line.fill.background()

    # Thanh màu xanh công nghệ trang trí bên trái
    bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.4), prs.slide_height)
    bar1.fill.solid()
    bar1.fill.fore_color.rgb = BLUE_ACCENT
    bar1.line.fill.background()

    # Logo HUCE nổi bật góc trên bên phải
    if os.path.exists(LOGO_HUCE):
        s1.shapes.add_picture(LOGO_HUCE, Inches(11.2), Inches(0.6), width=Inches(1.5))

    # Tên trường và Khoa
    tx_uni = s1.shapes.add_textbox(Inches(0.9), Inches(0.6), Inches(9.8), Inches(0.9))
    tf_uni = tx_uni.text_frame
    p1 = tf_uni.paragraphs[0]
    p1.text = "TRƯỜNG ĐẠI HỌC XÂY DỰNG HÀ NỘI"
    p1.font.name = "Arial"
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(186, 230, 253)

    p2 = tf_uni.add_paragraph()
    p2.text = "KHOA CÔNG NGHỆ THÔNG TIN · BỘ MÔN KHOA HỌC MÁY TÍNH"
    p2.font.name = "Arial"
    p2.font.size = Pt(13)
    p2.font.color.rgb = RGBColor(148, 163, 184)

    # Tên học phần
    tx_hp = s1.shapes.add_textbox(Inches(0.9), Inches(1.8), Inches(10.0), Inches(0.4))
    p_hp = tx_hp.text_frame.paragraphs[0]
    p_hp.text = "HỌC PHẦN: THỰC TẬP TỐT NGHIỆP (HỌC KỲ 1 - NĂM HỌC 2026-2027)"
    p_hp.font.name = "Arial"
    p_hp.font.size = Pt(13)
    p_hp.font.bold = True
    p_hp.font.color.rgb = RGBColor(56, 189, 248)

    # Tiêu đề báo cáo
    tx_rep = s1.shapes.add_textbox(Inches(0.9), Inches(2.3), Inches(11.2), Inches(1.8))
    tf_rep = tx_rep.text_frame
    tf_rep.word_wrap = True
    p_rep = tf_rep.paragraphs[0]
    p_rep.text = "BÁO CÁO TỔNG KẾT THỰC TẬP TỐT NGHIỆP"
    p_rep.font.name = "Arial"
    p_rep.font.size = Pt(28)
    p_rep.font.bold = True
    p_rep.font.color.rgb = WHITE

    p_sub = tf_rep.add_paragraph()
    p_sub.text = "THAM GIA PHÁT TRIỂN HỆ THỐNG BÁO CÁO ĐIỆN TỬ eFORM BTP\nVÀ NGHIÊN CỨU MODULE IMPORT EXCEL THÔNG MINH ÁP DỤNG AI"
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(18)
    p_sub.font.bold = True
    p_sub.font.color.rgb = RGBColor(224, 231, 255)

    # Thẻ thông tin sinh viên & đơn vị
    info_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(4.5), Inches(11.5), Inches(2.3))
    info_card.fill.solid()
    info_card.fill.fore_color.rgb = RGBColor(15, 23, 42)
    info_card.line.color.rgb = RGBColor(51, 65, 85)
    info_card.line.width = Pt(1)

    tx_c1 = s1.shapes.add_textbox(Inches(1.2), Inches(4.7), Inches(5.3), Inches(1.9))
    tf_c1 = tx_c1.text_frame
    p_i1 = tf_c1.paragraphs[0]
    p_i1.text = "Sinh viên thực hiện: Trần Văn Hoàng"
    p_i1.font.bold = True
    p_i1.font.size = Pt(14)
    p_i1.font.color.rgb = WHITE
    for label, val in [("Mã số sinh viên:", "0034467"), ("Lớp chuyên ngành:", "67CS - Khóa K67"), ("Ngành đào tạo:", "Khoa học máy tính")]:
        p = tf_c1.add_paragraph()
        p.text = f"{label} {val}"
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(203, 213, 225)

    tx_c2 = s1.shapes.add_textbox(Inches(6.8), Inches(4.7), Inches(5.3), Inches(1.9))
    tf_c2 = tx_c2.text_frame
    p_i2 = tf_c2.paragraphs[0]
    p_i2.text = "Cơ quan thực tập: Công ty TNHH Nền tảng chuyển đổi số VN"
    p_i2.font.bold = True
    p_i2.font.size = Pt(14)
    p_i2.font.color.rgb = WHITE
    for label, val in [("Cán bộ hướng dẫn (ĐVTT):", "Đào Đức Văn (Technical Lead - Bkav eGov)"), ("Giảng viên hướng dẫn:", "TS. Hoàng Nam Thắng (Khoa CNTT - HUCE)"), ("Thời gian thực tập:", "03/08/2026 - 16/10/2026 (11 tuần)")]:
        p = tf_c2.add_paragraph()
        p.text = f"{label} {val}"
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(203, 213, 225)

    # =========================================================================
    # SLIDE 2: LỜI CẢM ƠN
    # =========================================================================
    s2 = create_base_slide(prs, "LỜI CẢM ƠN", "TRANG BÌA VÀ LỜI CẢM ƠN", 2)
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "TRƯỜNG ĐẠI HỌC XÂY DỰNG HÀ NỘI (HUCE)")
    tx = s2.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Em xin bày tỏ lòng biết ơn sâu sắc đến:"
    p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = NAVY_PRIMARY
    items_huce = [
        ("Ban Giám hiệu & Khoa Công nghệ thông tin", "Đã tạo điều kiện thuận lợi và xây dựng chương trình đào tạo chuẩn mực để sinh viên được tiếp cận thực tế doanh nghiệp."),
        ("Bộ môn Khoa học máy tính", "Đã trang bị cho em nền tảng kiến thức vững chắc về cấu trúc dữ liệu, giải thuật, công nghệ phần mềm và trí tuệ nhân tạo."),
        ("Giảng viên hướng dẫn: TS. Hoàng Nam Thắng", "Thầy đã tận tình hướng dẫn, định hướng học thuật, theo sát tiến độ và động viên em trong suốt quá trình triển khai thực tập.")
    ]
    for h, b in items_huce:
        p1 = tf.add_paragraph(); p1.text = "• " + h + ":"; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(12); p2.font.color.rgb = SLATE_DARK

    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "CÔNG TY TNHH NỀN TẢNG CHUYỂN ĐỔI SỐ VIỆT NAM")
    tx2 = s2.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "Em xin trân trọng cảm ơn:"
    p.font.size = Pt(13); p.font.bold = True; p.font.color.rgb = NAVY_PRIMARY
    items_cty = [
        ("Ban Lãnh đạo Công ty (DXP VN) & Khối eGov", "Đã tiếp nhận và tạo môi trường làm việc chuyên nghiệp, trang bị máy trạm và cơ sở hạ tầng phục vụ nghiên cứu phát triển."),
        ("Cán bộ hướng dẫn: Anh Đào Đức Văn (Technical Lead)", "Đã trực tiếp giao nhiệm vụ, chỉ bảo phương pháp giải quyết vấn đề trên hệ thống lớn, kiểm tra và nghiệm thu các sản phẩm kỹ thuật."),
        ("Nhóm kỹ sư phát triển eForm BTP", "Đã nhiệt tình phối hợp, chia sẻ kinh nghiệm xử lý dữ liệu Datamart, tối ưu hệ thống và hỗ trợ em hoàn thành tốt các nhiệm vụ được giao.")
    ]
    for h, b in items_cty:
        p1 = tf2.add_paragraph(); p1.text = "• " + h + ":"; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(12); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 3: MỤC LỤC & DANH MỤC HÌNH BẢNG
    # =========================================================================
    s3 = create_base_slide(prs, "MỤC LỤC BÁO CÁO VÀ DANH MỤC MINH CHỨNG", "TỔNG QUAN NỘI DUNG", 3)
    add_card(s3, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "CẤU TRÚC 6 PHẦN BÁO CÁO CHÍNH")
    tx = s3.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    parts = [
        ("Phần 1. Giới thiệu chung về đơn vị thực tập", "Lịch sử hình thành, cơ cấu tổ chức, lĩnh vực hoạt động và dự án eForm BTP."),
        ("Phần 2. Mục tiêu và kế hoạch thực tập", "Mục tiêu theo 4 Chuẩn đầu ra (CLO) và kế hoạch chi tiết 11 tuần công tác."),
        ("Phần 3. Nội dung và kết quả thực tập", "Chi tiết công việc dự án eForm, phát triển Module AI Import, sản phẩm kỹ thuật."),
        ("Phần 4. Phân tích, đánh giá và đề xuất", "Quy trình công việc, khó khăn và giải pháp, liên hệ lý thuyết HUCE và thực tế."),
        ("Phần 5. Tự nhận xét và định hướng cá nhân", "Đánh giá năng lực bản thân, điểm mạnh/yếu, định hướng nghề nghiệp."),
        ("Phần 6. Kết luận và kiến nghị", "Tổng kết kết quả 11 tuần thực tập, bài học kinh nghiệm và kiến nghị chuyển giao.")
    ]
    for p_title, p_desc in parts:
        p_t = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p_t.text = p_title; p_t.font.bold = True; p_t.font.size = Pt(12); p_t.font.color.rgb = NAVY_PRIMARY
        p_d = tf.add_paragraph(); p_d.text = "  - " + p_desc; p_d.font.size = Pt(11); p_d.font.color.rgb = SLATE_MUTED

    add_card(s3, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "DANH MỤC HÌNH ẢNH & MINH CHỨNG TRỌNG TÂM")
    tx2 = s3.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    figs = [
        ("Hình 1 & 2", "Giao diện Tra cứu văn bản & Xuất file nén ZIP hàng loạt (Tuần 3)."),
        ("Hình 3 & 4", "Cấu hình quy trình Workflow & Tiện ích Toàn màn hình (Tuần 4)."),
        ("Hình 5 & 6", "Phân lập thẻ DOM biểu 11b & Bảo toàn dữ liệu nhập tay biểu 04c (Tuần 5)."),
        ("Hình 7 & 8", "Lưu DocumentContent & Nhấp đúp mở báo cáo con theo DocumentId (Tuần 6)."),
        ("Hình 9 & 10", "Giao diện Upload AJAX kéo thả & Cố định thứ tự đơn vị Stored Proc (Tuần 7)."),
        ("Hình 11 & 12", "Cố định danh mục xã & Xuất template nhúng công thức tự động (Tuần 8)."),
        ("Hình 13 & 14", "Tối ưu nạp biểu tổng hợp qua Redis Cache & Vòng lặp Cache tự học (Tuần 9)."),
        ("Hình 15 & 16", "Giao báo cáo đa cấp cho 3.321 xã & Kiểm thử toàn trình End-to-End (Tuần 10)."),
        ("Hình 17 & 18", "Sidebar hiển thị số lượng, Chặn quyền sửa & Buổi Showcase Mentor (Tuần 11).")
    ]
    for f_name, f_desc in figs:
        p_f = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p_f.text = f"• {f_name}: {f_desc}"
        p_f.font.size = Pt(11); p_f.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 4: PHẦN 1 - GIỚI THIỆU ĐƠN VỊ THỰC TẬP
    # =========================================================================
    s4 = create_base_slide(prs, "GIỚI THIỆU CHUNG VỀ ĐƠN VỊ THỰC TẬP", "PHẦN 1: ĐƠN VỊ THỰC TẬP", 4)
    add_card(s4, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "PHÁP NHÂN & LỊCH SỬ HÌNH THÀNH")
    tx = s4.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    company_facts = [
        ("Tên đầy đủ:", "CÔNG TY TNHH NỀN TẢNG CHUYỂN ĐỔI SỐ VIỆT NAM"),
        ("Tên quốc tế:", "VIET NAM DIGITAL TRANSFORMATION PLATFORM CO., LTD (DXP VN)"),
        ("Mã số thuế:", "0110210137 (Cấp ngày 19/12/2022 bởi Sở KH&ĐT TP. Hà Nội)"),
        ("Trụ sở chính:", "Tầng 2, Tòa nhà HH1, KĐT Yên Hòa, đường Dương Đình Nghệ, P. Yên Hòa, Q. Cầu Giấy, TP. Hà Nội"),
        ("Hệ sinh thái:", "Là đơn vị công nghệ thành viên chuyên trách triển khai các giải pháp Chính phủ số và Doanh nghiệp số trong hệ sinh thái Tập đoàn Bkav"),
        ("Sứ mệnh cốt lõi:", "Phát triển các nền tảng số hóa theo kiến trúc lấy dữ liệu làm trung tâm (Data-Centric), thúc đẩy cải cách hành chính và chuyển đổi số quốc gia")
    ]
    for label, val in company_facts:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = label; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf.add_paragraph(); p2.text = "  " + val; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s4, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "CƠ CẤU TỔ CHỨC & BỘ PHẬN THỰC TẬP")
    tx2 = s4.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    org_structure = [
        ("Ban Giám đốc Công ty", "Điều hành chiến lược kinh doanh và định hướng nghiên cứu phát triển các giải pháp số hóa quốc gia."),
        ("Khối Chính phủ số (eGov)", "Khối chuyên môn tập trung phát triển các phần mềm quản trị công, văn phòng điện tử, hệ thống báo cáo điện tử cho các Bộ, ban, ngành."),
        ("Phòng Phát triển Hệ thống eGov Solutions", "Nơi sinh viên trực tiếp thực tập; chuyên trách thiết kế kiến trúc, lập trình Backend (.NET), Frontend và tích hợp các module chuyển đổi số."),
        ("Phòng Đảm bảo Chất lượng (QA/QC)", "Xây dựng kịch bản kiểm thử, kiểm thử tải, kiểm tra tuân thủ bảo mật và nghiệm thu chức năng trước khi phát hành."),
        ("Bộ phận Quản trị Hạ tầng & Vận hành (DevOps)", "Quản trị cụm máy chủ ứng dụng IIS, hệ cơ sở dữ liệu MySQL/Datamart, hệ thống đệm phân tán Redis và hạ tầng bảo mật.")
    ]
    for unit, desc in org_structure:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = "• " + unit; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf2.add_paragraph(); p2.text = "  " + desc; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 5: PHẦN 1 - LĨNH VỰC HOẠT ĐỘNG VÀ DỰ ÁN eFORM BTP
    # =========================================================================
    s5 = create_base_slide(prs, "LĨNH VỰC HOẠT ĐỘNG VÀ DỰ ÁN THAM GIA", "PHẦN 1: ĐƠN VỊ THỰC TẬP", 5)
    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "HỆ SINH THÁI GIẢI PHÁP SỐ HÓA")
    tx = s5.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    ecosystem = [
        ("BkavDX eGov (Chính phủ điện tử)", "Hệ thống quản lý văn bản, điều hành công việc và chỉ đạo điều hành liên thông 4 cấp hành chính."),
        ("BkavDX eCabinet (Phòng họp không giấy)", "Giải pháp quản lý phiên họp trực tuyến, biểu quyết điện tử và tra cứu tài liệu số cho các cơ quan nhà nước."),
        ("Nền tảng tích hợp LGSP / Data Exchange", "Trục kết nối, chia sẻ dữ liệu liên ngành phục vụ xây dựng CSDL quốc gia."),
        ("Nền tảng Báo cáo điện tử (eForm / eReport)", "Số hóa toàn diện các biểu mẫu báo cáo thống kê chuyên ngành, thu thập số liệu tự động và phân tích chỉ số kinh tế - xã hội.")
    ]
    for p_name, p_desc in ecosystem:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + p_name; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + p_desc; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "DỰ ÁN: HỆ THỐNG BÁO CÁO ĐIỆN TỬ eFORM BTP")
    tx2 = s5.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    project_btp = [
        ("Khách hàng & Đơn vị chủ quản:", "Bộ Tư pháp Việt Nam (Cục Kế hoạch - Tài chính chủ trì điều phối số liệu thống kê ngành)."),
        ("Cổng thông tin chính thức:", "https://baocaothongke.moj.gov.vn và https://thongke.moj.gov.vn"),
        ("Môi trường thử nghiệm dự án:", "https://baocao-btp.demozone.vn:8443"),
        ("Phạm vi triển khai trên toàn quốc:", "Bao trùm 100% các đơn vị thuộc Bộ Tư pháp, 63 Sở Tư pháp tỉnh/thành phố, các Phòng Tư pháp huyện và hàng nghìn UBND cấp xã/phường."),
        ("Nhiệm vụ cốt lõi:", "Số hóa hơn 27 mẫu biểu báo cáo thống kê phức tạp (hộ tịch, quốc tịch, công chứng, luật sư, thi hành án dân sự, bồi thường nhà nước...), phục vụ thu thập và tổng hợp số liệu kỳ 6 tháng, 1 năm.")
    ]
    for label, val in project_btp:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = label; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + val; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 6: PHẦN 2 - MỤC TIÊU THỰC TẬP THEO CHUẨN ĐẦU RA (CLO)
    # =========================================================================
    s6 = create_base_slide(prs, "MỤC TIÊU HỌC TẬP CÁ NHÂN THEO CHUẨN ĐẦU RA (CLO)", "PHẦN 2: MỤC TIÊU & KẾ HOẠCH", 6)
    clos = [
        ("CLO 1: Vận dụng kiến thức chuyên ngành CNTT vào thực tiễn",
         "Áp dụng kiến thức về công nghệ phần mềm, cấu trúc dữ liệu, cơ sở dữ liệu quan hệ và giải thuật học máy đã được đào tạo tại Trường ĐH Xây dựng Hà Nội để giải quyết các bài toán kỹ thuật phức tạp trong môi trường phần mềm doanh nghiệp cấp Bộ.",
         Inches(0.8), Inches(1.5), Inches(5.7), Inches(2.5)),
        ("CLO 2: Nắm vững kỹ thuật lập trình và công nghệ hiện đại",
         "Thành thạo công nghệ Backend C# (.NET Framework 4.8 / ASP.NET MVC / Web API 2), tối ưu hóa truy vấn CSDL Datamart (MySQL/Stored Procedure), tích hợp bộ nhớ đệm phân tán Redis Cache và phát triển dịch vụ AI bằng Python (FastAPI, PyTorch, Compact U-Net).",
         Inches(6.8), Inches(1.5), Inches(5.7), Inches(2.5)),
        ("CLO 3: Rèn luyện kỹ năng làm việc nhóm và quy trình công nghiệp",
         "Làm quen và tuân thủ quy trình phát triển phần mềm chuẩn mực: quản lý tiến độ bằng eTask/Jira, kiểm soát phiên bản mã nguồn bằng Git/GitLab (nhánh tính năng, commit chuẩn, Merge Request), viết tài liệu kỹ thuật và báo cáo định kỳ.",
         Inches(0.8), Inches(4.3), Inches(5.7), Inches(2.5)),
        ("CLO 4: Đạo đức nghề nghiệp và tác phong làm việc trách nhiệm",
         "Chấp hành nghiêm chỉnh nội quy đơn vị thực tập, bảo mật dữ liệu hành chính công vụ của Bộ Tư pháp, đảm bảo an toàn hệ thống khi thao tác trên CSDL thật, chủ động nghiên cứu giải pháp và giữ tinh thần cầu thị học hỏi.",
         Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.5))
    ]
    for clo_title, clo_content, left, top, w, h in clos:
        add_card(s6, left, top, w, h, clo_title)
        tx = s6.shapes.add_textbox(left + Inches(0.2), top + Inches(0.6), w - Inches(0.4), h - Inches(0.7))
        p = tx.text_frame.paragraphs[0]
        p.text = clo_content
        p.font.size = Pt(12)
        p.font.color.rgb = SLATE_DARK
        p.alignment = PP_ALIGN.JUSTIFY

    # =========================================================================
    # SLIDE 7: PHẦN 2 - KẾ HOẠCH CÔNG VIỆC CHI TIẾT (TUẦN 1 - TUẦN 6)
    # =========================================================================
    s7 = create_base_slide(prs, "KẾ HOẠCH CÔNG VIỆC CHI TIẾT (TUẦN 1 - TUẦN 6)", "PHẦN 2: MỤC TIÊU & KẾ HOẠCH", 7)
    tbl_shape = s7.shapes.add_table(7, 4, Inches(0.8), Inches(1.5), Inches(11.73), Inches(5.2))
    table = tbl_shape.table
    col_widths = [Inches(1.2), Inches(3.6), Inches(4.5), Inches(2.4)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    headers = ["Thời gian", "Nội dung công việc dự kiến", "Kết quả mong đợi", "Hình thức minh chứng"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True; p.font.size = Pt(12); p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    plan_w1_6 = [
        ("Tuần 1\n(03-07/08)", "Tìm hiểu quy trình làm việc eTask/Git, kiến trúc eForm BTP (.NET MVC, MySQL), dựng Local Dev.", "Nắm vững luồng dữ liệu hệ thống, dựng thành công môi trường phát triển cục bộ.", "Ảnh dự án chạy trên IIS, eTask, Visual Studio"),
        ("Tuần 2\n(10-14/08)", "Khảo sát bài toán Import Excel đa cấu trúc, phân tích mô hình AI, thiết kế System Design & Data Flow.", "Chốt kiến trúc hệ thống, lựa chọn hướng tiếp cận và thống nhất phương án với Mentor.", "Tài liệu đề xuất (Biểu 1), Sơ đồ kiến trúc & Data Flow"),
        ("Tuần 3\n(17-21/08)", "Sửa lỗi hiển thị sai đơn vị khởi tạo; viết tính năng tải hàng loạt file Excel ZIP; chia dataset theo họ bố cục.", "Phân hệ tra cứu chuẩn xác 100%, xuất tệp ZIP an toàn; ngăn chặn rò rỉ dữ liệu AI.", "Ảnh GitLab, Ảnh giao diện tra cứu & xuất tệp ZIP"),
        ("Tuần 4\n(24-28/08)", "Sửa lỗi chuyển trả lại sai người trong Workflow; cấu hình kiểm tra logic; sửa validate nạp Excel; làm Fullscreen.", "Luồng quy trình chuẩn xác, mở rộng không gian 100% diện tích làm việc; mở rộng dataset AI.", "Ảnh quy trình Workflow, Cấu hình logic, Ảnh Fullscreen"),
        ("Tuần 5\n(31/08-04/09)", "Sửa lỗi #REF Datamart; phân lập DOM biểu 11b (tabSuffix); giữ dữ liệu nhập tay 04c; train Compact U-Net.", "Không còn lỗi #REF, mở 2 biểu con không mất Form 2, giữ nguyên dữ liệu tay; API FastAPI JSON 2.0.", "Ảnh biểu 11b, Biểu 04c, Đồ thị train & Swagger UI"),
        ("Tuần 6\n(07-11/09)", "Tự lưu DocumentContent; click đúp mở báo cáo con theo DocumentId; nâng font 14px; tích hợp Backend C#.", "Mở báo cáo con tức thì, giao diện chuẩn công thái học; C# gọi thành công dịch vụ AI.", "Ảnh DocumentContent, Mở tab con 1.1, Báo cáo kiểm thử")
    ]
    for i, row in enumerate(plan_w1_6):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11); p.font.color.rgb = SLATE_DARK
            if j == 0:
                p.alignment = PP_ALIGN.CENTER; p.font.bold = True

    # =========================================================================
    # SLIDE 8: PHẦN 2 - KẾ HOẠCH CÔNG VIỆC CHI TIẾT (TUẦN 7 - TUẦN 11)
    # =========================================================================
    s8 = create_base_slide(prs, "KẾ HOẠCH CÔNG VIỆC CHI TIẾT (TUẦN 7 - TUẦN 11)", "PHẦN 2: MỤC TIÊU & KẾ HOẠCH", 8)
    tbl_shape2 = s8.shapes.add_table(6, 4, Inches(0.8), Inches(1.5), Inches(11.73), Inches(5.2))
    table2 = tbl_shape2.table
    for i, w in enumerate(col_widths):
        table2.columns[i].width = w

    for j, h in enumerate(headers):
        cell = table2.cell(0, j)
        cell.text = h
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True; p.font.size = Pt(12); p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    plan_w7_11 = [
        ("Tuần 7\n(14-18/09)", "Khóa cột 1,2,8 biểu 11b; sửa mất ghi chú nộp bổ sung (fact_Note); cố định thứ tự đơn vị; dựng Upload AJAX.", "Khóa cứng cột trong CSDL, ghi chú lên biểu tổng hợp đầy đủ; giao diện kéo thả tệp không tải lại trang.", "Ảnh ghi chú Form 2, Cố định đơn vị, 16 ca test UI"),
        ("Tuần 8\n(21-25/09)", "Cố định 100% xã bằng LEFT JOIN; xuất template Excel có công thức toán; dựng lưới Preview Handsontable.", "Bảo toàn danh mục xã sau khi chốt số; tệp mẫu có công thức; hiển thị trung thực 6 tầng header, 78 ô gộp.", "Ảnh biểu tổng hợp xã, Template Excel, Lưới Preview"),
        ("Tuần 9\n(28/09-02/10)", "Tối ưu nạp biểu bằng Redis Cache; lập checklist test QA; cấu hình Admin 3 khối; dọn dẹp DB; Cache tự học.", "Mở biểu nhanh >80%; bàn giao 5 kịch bản test QA; dọn sạch DB thật; cơ chế tự học 2 tầng giảm tải gọi AI.", "Đo hiệu năng Redis, Cấu hình Admin, 3/3 test tự học"),
        ("Tuần 10\n(05-09/10)", "Sửa giao báo cáo hàng loạt 3 cấp cho 3.321 xã; tạo môi trường test kỳ sơ bộ; phòng vệ file rác & lưu API.", "Phát hành cây báo cáo 3 cấp thông suốt; tạo 6 tài khoản test; kiểm thử End-to-End 100% không xung đột eForm.", "Ảnh giao 3.321 xã, Kỳ sơ bộ test, 12 ca test E2E"),
        ("Tuần 11\n(12-16/10)", "Sửa lỗi Sidebar mất highlight & mất badge; chặn quyền sửa người duyệt; tổ chức Showcase với Mentor.", "Sidebar hiển thị chuẩn 91 báo cáo con, khóa quyền sửa tài khoản duyệt; Mentor nghiệm thu đạt loại Xuất sắc.", "Ảnh Sidebar, Chặn quyền sửa, Minh chứng Showcase")
    ]
    for i, row in enumerate(plan_w7_11):
        for j, val in enumerate(row):
            cell = table2.cell(i + 1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11); p.font.color.rgb = SLATE_DARK
            if j == 0:
                p.alignment = PP_ALIGN.CENTER; p.font.bold = True

    # =========================================================================
    # SLIDE 9: PHẦN 3 - KẾT QUẢ DỰ ÁN eFORM BTP (GIAI ĐOẠN 1: TUẦN 1 - 5)
    # =========================================================================
    s9 = create_base_slide(prs, "KẾT QUẢ DỰ ÁN eFORM BTP: NGHIỆP VỤ & SỬA LỖI HỆ THỐNG", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 9)
    tasks_phase1 = [
        ("Tra cứu & Xuất dữ liệu hàng loạt (Tuần 3)",
         "Sự cố: Phân hệ tra cứu hiển thị sai đơn vị khởi tạo do thuật toán cắt chuỗi phòng ban bị nhầm định danh cá nhân.\n"
         "Xử lý: Hiệu chỉnh truy vấn danh bạ phòng ban theo mã đơn vị gốc, phân tách độc lập giữa cơ quan ban hành và người lập.\n"
         "Tính năng mới: Phát triển menu Xuất file tải hàng loạt biểu mẫu Excel nén ZIP theo lô, giải phóng bộ nhớ an toàn."),
        ("Quy trình Workflow & Tiện ích Fullscreen (Tuần 4)",
         "Sự cố: Thao tác trả lại báo cáo bị chuyển sai người nhận do đứt gãy liên kết Transition Node trong bảng quy trình CSDL.\n"
         "Xử lý: Cập nhật lại cấu hình nút trong CSDL, khôi phục luồng trả về đúng người lập biểu (chị Đặng Thị Thu Trang).\n"
         "Tiện ích: Xây dựng chế độ Toàn màn hình (Fullscreen Overlay) mở rộng 100% diện tích hiển thị, hỗ trợ phím Esc."),
        ("Truy vấn Datamart & Phân lập DOM Biểu đa 11b (Tuần 5)",
         "Sự cố #REF: Công thức =Sum(...) trong CSDL Datamart bị lệch khoảng dòng và bỏ sót dữ liệu đơn vị cấp xã.\n"
         "Xử lý Datamart: Khai triển chính xác khoảng dòng công thức cho văn bản cha/con, khôi phục 100% số liệu cấp xã.\n"
         "Phân lập thẻ DOM: Gắn hậu tố tabSuffix (DocumentId) cho từng iframe, khắc phục triệt để lỗi mất Form 2 ghi chú.")
    ]
    for i, (t_title, t_body) in enumerate(tasks_phase1):
        left = Inches(0.8 + i * 4.0)
        add_card(s9, left, Inches(1.5), Inches(3.73), Inches(5.2), t_title)
        tx = s9.shapes.add_textbox(left + Inches(0.15), Inches(2.1), Inches(3.43), Inches(4.4))
        tf = tx.text_frame; tf.word_wrap = True
        for line in t_body.split('\n'):
            p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
            if ":" in line:
                parts = line.split(":", 1)
                p.text = parts[0] + ":"
                p.font.bold = True
                p.font.size = Pt(11)
                p.font.color.rgb = BLUE_ACCENT if "Tính năng" in line or "Tiện ích" in line else (RED_ACCENT if "Sự cố" in line else NAVY_PRIMARY)
                p2 = tf.add_paragraph()
                p2.text = parts[1].strip()
                p2.font.size = Pt(11)
                p2.font.color.rgb = SLATE_DARK
                p2.alignment = PP_ALIGN.JUSTIFY

    # =========================================================================
    # SLIDE 10: PHẦN 3 - KẾT QUẢ DỰ ÁN eFORM BTP (GIAI ĐOẠN 2: TUẦN 6 - 8)
    # =========================================================================
    s10 = create_base_slide(prs, "KẾT QUẢ DỰ ÁN eFORM BTP: TỐI ƯU CƠ SỞ DỮ LIỆU & BẢNG BIỂU", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 10)
    tasks_phase2 = [
        ("Bảo toàn dữ liệu nhập tay Biểu 04c & Mở tab con (Tuần 6)",
         "Sự cố: Người dùng bấm 'Tổng hợp lại dữ liệu' làm mất trắng số liệu nhập tay do dữ liệu tạm trên client chưa lưu vào server.\n"
         "Xử lý: Xây dựng cơ chế đánh chặn (Interceptor), tự động lưu dữ liệu nhập tay vào trường DocumentContent trước khi tổng hợp.\n"
         "Mở tab con: Gắn DocumentId vào thẻ hàng, nhấp đúp mở ngay báo cáo con chi tiết ra tab 1.1 song song."),
        ("Đồng bộ Ghi chú & Cố định thứ tự đơn vị (Tuần 7)",
         "Sự cố mất ghi chú: Luồng nộp bổ sung bỏ sót ghi nhận vào bảng fact_Note, khiến biểu tổng hợp bị mất phần giải trình.\n"
         "Xử lý: Tạo mới bản ghi trong fact_Note theo DocumentVersionId, cập nhật thủ tục ETL đồng bộ sang Datamart.\n"
         "Cố định thứ tự: Thay đổi mệnh đề sắp xếp Stored Procedure từ thời gian sang phân cấp OrgHierarchyLevel và OrgCode."),
        ("Cố định danh mục xã & Xuất Template có công thức (Tuần 8)",
         "Sự cố mất dòng xã: Khi chốt số liệu, phép nối INNER JOIN tự loại bỏ các xã chưa nộp, làm nhảy số thứ tự biểu tổng hợp.\n"
         "Xử lý: Chuyển sang phép LEFT JOIN với bảng danh mục chuẩn, bảo toàn 100% dòng các xã chưa nộp kèm dấu gạch '-'.\n"
         "Template có công thức: Đọc SourceData backend, dịch chuyển tọa độ dòng, nhúng công thức tự động tính tổng khi tải về.")
    ]
    for i, (t_title, t_body) in enumerate(tasks_phase2):
        left = Inches(0.8 + i * 4.0)
        add_card(s10, left, Inches(1.5), Inches(3.73), Inches(5.2), t_title)
        tx = s10.shapes.add_textbox(left + Inches(0.15), Inches(2.1), Inches(3.43), Inches(4.4))
        tf = tx.text_frame; tf.word_wrap = True
        for line in t_body.split('\n'):
            if ":" in line:
                parts = line.split(":", 1)
                p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
                p.text = parts[0] + ":"
                p.font.bold = True; p.font.size = Pt(11)
                p.font.color.rgb = BLUE_ACCENT if "Mở tab" in line or "Template" in line else (RED_ACCENT if "Sự cố" in line else NAVY_PRIMARY)
                p2 = tf.add_paragraph()
                p2.text = parts[1].strip(); p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK
                p2.alignment = PP_ALIGN.JUSTIFY

    # =========================================================================
    # SLIDE 11: PHẦN 3 - KẾT QUẢ DỰ ÁN eFORM BTP (GIAI ĐOẠN 3: TUẦN 9 - 11)
    # =========================================================================
    s11 = create_base_slide(prs, "KẾT QUẢ DỰ ÁN eFORM BTP: HIỆU NĂNG, PHÂN CẤP & BÀN GIAO", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 11)
    tasks_phase3 = [
        ("Tối ưu hiệu năng với Redis Cache (Tuần 9)",
         "Hiện trạng cũ: Mở biểu tổng hợp cấp tỉnh/huyện mất từ 5-10 giây do câu lệnh SQL phức tạp và quét bảng lớn liên tục.\n"
         "Giải pháp: Tích hợp Redis Cache phân tán theo mô hình Cache-Aside, khóa cache theo định danh report:aggregate:{docTypeId}.\n"
         "Hiệu quả: Thời gian nạp biểu giảm mạnh xuống 0,5 - 1,2 giây (giảm >80%), giảm tải I/O cho máy chủ CSDL."),
        ("Giao báo cáo 3 cấp cho 3.321 xã (Tuần 10)",
         "Sự cố: Tính năng giao báo cáo hàng loạt bị lỗi không phân rã được chuỗi báo cáo 3 cấp (cha 01, con 01b, cấp 3 01a).\n"
         "Xử lý: Tái cấu trúc logic phân rã cây đơn vị; phát hành thành công từ Cục Kế hoạch - Tài chính xuống 3.321 xã của 34 Sở.\n"
         "Môi trường test: Tạo 3 tài khoản cục, 3 tài khoản xã, mở kỳ sơ bộ 2026 sẵn sàng cho các đơn vị kiểm thử."),
        ("Sửa lỗi Sidebar & Chặn quyền sửa (Tuần 11)",
         "Sidebar: Khắc phục lỗi mất highlight và mất badge số lượng sau phiên làm việc dài; hiển thị chính xác 91 báo cáo con.\n"
         "Chặn quyền sửa: Trên danh sách báo cáo bị trả lại, so khớp userId != UserCreatedId để ẩn nút sửa với tài khoản người duyệt.\n"
         "Nghiệm thu: Tổ chức thành công buổi Showcase demo tính năng với Mentor Đào Đức Văn và nhóm eGov Solutions.")
    ]
    for i, (t_title, t_body) in enumerate(tasks_phase3):
        left = Inches(0.8 + i * 4.0)
        add_card(s11, left, Inches(1.5), Inches(3.73), Inches(5.2), t_title)
        tx = s11.shapes.add_textbox(left + Inches(0.15), Inches(2.1), Inches(3.43), Inches(4.4))
        tf = tx.text_frame; tf.word_wrap = True
        for line in t_body.split('\n'):
            if ":" in line:
                parts = line.split(":", 1)
                p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
                p.text = parts[0] + ":"
                p.font.bold = True; p.font.size = Pt(11)
                p.font.color.rgb = BLUE_ACCENT if "Hiệu quả" in line or "Nghiệm thu" in line else (RED_ACCENT if "Hiện trạng" in line or "Sự cố" in line else NAVY_PRIMARY)
                p2 = tf.add_paragraph()
                p2.text = parts[1].strip(); p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK
                p2.alignment = PP_ALIGN.JUSTIFY

    # =========================================================================
    # SLIDE 12: PHẦN 3 - ĐỀ TÀI CÁ NHÂN MODULE AI IMPORT (KIẾN TRÚC & MÔ HÌNH)
    # =========================================================================
    s12 = create_base_slide(prs, "MODULE IMPORT EXCEL THÔNG MINH: KIẾN TRÚC VÀ MÔ HÌNH AI", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 12)
    add_card(s12, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "ĐẶT VẤN ĐỀ & KIẾN TRÚC HỆ THỐNG")
    tx = s12.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    ai_arch = [
        ("Thách thức thực tế:", "Các đơn vị gửi bảng tính Excel có tiêu đề đa tầng (4-6 cấp), ô gộp phức tạp, dòng ghi chú và chữ ký làm hỏng các bộ nạp dữ liệu truyền thống."),
        ("Nguyên tắc phân định:", "AI chỉ hỗ trợ nhận diện và trích xuất cấu trúc thô; Backend C# chịu trách nhiệm kiểm tra nghiệp vụ và lưu trữ; AI không có quyền ghi trực tiếp vào CSDL."),
        ("Kiến trúc phân tầng độc lập:", "Frontend (Upload AJAX, Handsontable) -> Backend C# (.NET Framework 4.8 / ImportService) -> AI Service (Python FastAPI) -> Lưu trữ an toàn (Entity Framework 6 / SQL Server LocalDB / eForm)."),
        ("Hợp đồng dữ liệu JSON 2.0:", "Quy chuẩn siêu dữ liệu định danh, danh sách bảng, mảng ô gộp, đường dẫn tiêu đề đa tầng (headerPath) và phân cấp cây chỉ tiêu (hierarchyPath).")
    ]
    for h, b in ai_arch:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s12, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "MÔ HÌNH HỌC SÂU & HẬU XỬ LÝ DỮ LIỆU")
    tx2 = s12.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    ai_model = [
        ("Chống rò rỉ dữ liệu (Layout Fingerprint):", "Gom cụm bảng theo 'vân tay bố cục' hình học; đảm bảo các file cùng template chỉ nằm trong duy nhất một tập Train/Val/Test, ngăn chặn Overfitting."),
        ("Mô hình Compact U-Net (PyTorch CPU):", "Mạng nơ-ron phân đoạn vùng Header Mask và Value Mask với 379.107 tham số nhẹ; huấn luyện qua 14 epoch với Early Stopping; F1-score Header đạt 94,82%, Value đạt 96,15%."),
        ("Thuật toán cắt tỉa footer-trim:", "Quét ngược từ đáy bảng để nhận diện và loại bỏ hoàn toàn các dòng ghi chú, căn cứ, nơi nhận và chữ ký thủ trưởng; khôi phục ranh giới bảng sạch 100%."),
        ("Chuẩn hóa cây phân cấp chỉ tiêu:", "Tự động duyệt và phân cấp thành Cấp 0 (Tổng số) -> Cấp 1 (I, II) -> Cấp 2 (1, 2) -> Cấp 3 (1.1, 1.2); đối chiếu 4.656 ô dữ liệu thực tế đạt độ chính xác 100%.")
    ]
    for h, b in ai_model:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 13: PHẦN 3 - ĐỀ TÀI CÁ NHÂN MODULE AI IMPORT (GIAO DIỆN & TỰ HỌC)
    # =========================================================================
    s13 = create_base_slide(prs, "MODULE IMPORT EXCEL THÔNG MINH: LƯỚI PREVIEW VÀ CACHE TỰ HỌC", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 13)
    add_card(s13, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "LƯỚI XEM TRƯỚC HANDSONTABLE ĐA CẤP")
    tx = s13.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    preview_features = [
        ("Tái hiện 100% hình thái Excel gốc:", "Ứng dụng Handsontable tái tạo trung thực 6 tầng tiêu đề lồng nhau và 78 khối ô gộp phức tạp của Biểu 21a mà không bị xô lệch vị trí."),
        ("Cố định tiêu đề & Cuộn hai chiều:", "Cố định 6 hàng tiêu đề trên cùng, cho phép cán bộ cuộn dọc qua hàng trăm dòng số liệu mà tiêu đề vẫn ghim vững chắc; thanh cuộn ngang mượt mà."),
        ("Chỉnh sửa trực tiếp trên ô (Inline Edit):", "Người dùng có thể nhấp đúp để sửa số liệu trực tiếp trên từng ô lưới; sự kiện afterChange tự động bắt tọa độ ô, giá trị cũ/mới và đánh dấu viền màu cam hổ phách."),
        ("Phòng vệ đầu vào đa lớp (Client-side):", "Chặn đứng file rỗng 0 byte, file quá 50MB, file sai đuôi .xlsx/.xlsm; kiểm tra Magic Bytes (PK header 0x50 0x4B) chống đổi đuôi giả mạo.")
    ]
    for h, b in preview_features:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s13, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "VÒNG LẶP CACHE TỰ HỌC (SELF-LEARNING LOOP)")
    tx2 = s13.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    cache_features = [
        ("Bản chất bài toán chi phí AI:", "Nếu mỗi lần tải bảng tính tương tự đều phải gọi toàn bộ tiến trình suy luận AI thì sẽ gây tiêu tốn tài nguyên máy chủ và độ trễ phản hồi."),
        ("Cơ chế lưu trữ đệm 2 tầng (Hybrid Cache):", "Khi người dùng xác nhận bản sửa, quy tắc được lưu tức thời tại LocalStorage (< 5ms) và đồng bộ lên Server ASP.NET qua API POST /api/import/feedback lưu vào ConcurrentDictionary."),
        ("Tự động áp dụng bản sửa:", "Khi người dùng nạp lại workbook tương tự, hệ thống tự đối soát Cache; nếu tìm thấy quy tắc đã học, hệ thống lập tức tự động điền bản sửa và hiển thị Banner xanh lá xác nhận."),
        ("Lưu trữ an toàn vào CSDL:", "Modal xác nhận tổng hợp số lượng ô chỉnh sửa trước khi gọi API POST /api/import/save ghi nhận an toàn vào CSDL, không gây xung đột với eForm cũ.")
    ]
    for h, b in cache_features:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 14: PHẦN 3 - TỔNG HỢP SẢN PHẨM KỸ THUẬT & MINH CHỨNG
    # =========================================================================
    s14 = create_base_slide(prs, "TỔNG HỢP CÁC SẢN PHẨM KỸ THUẬT VÀ KẾT QUẢ THỰC NGHIỆM", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 14)
    tbl_shape = s14.shapes.add_table(5, 4, Inches(0.8), Inches(1.5), Inches(11.73), Inches(3.2))
    table = tbl_shape.table
    c_w = [Inches(2.5), Inches(4.0), Inches(3.0), Inches(2.23)]
    for i, w in enumerate(c_w): table.columns[i].width = w

    t_headers = ["Hạng mục sản phẩm", "Chi tiết kỹ thuật đã thực hiện", "Quy mô / Dữ liệu thực tế", "Kết quả nghiệm thu"]
    for j, h in enumerate(t_headers):
        cell = table.cell(0, j); cell.text = h; cell.fill.solid(); cell.fill.fore_color.rgb = NAVY_PRIMARY
        p = cell.text_frame.paragraphs[0]; p.font.bold = True; p.font.size = Pt(12); p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    products = [
        ("Bản vá lỗi & Tính năng eForm BTP", "Sửa lỗi Datamart #REF, phân lập DOM 11b, bảo toàn nhập tay 04c, cố định danh mục xã, xuất template có công thức, giao 3 cấp.", "3.321 xã, 34 Sở Tư pháp, 63 tỉnh/thành phố, 27 mẫu biểu báo cáo", "ĐÃ TÍCH HỢP & HOẠT ĐỘNG ỔN ĐỊNH"),
        ("Dịch vụ Trích xuất AI (FastAPI)", "Mô hình Compact U-Net phân đoạn bảng, thuật toán footer-trim, chuẩn hóa lược đồ JSON Schema 2.0.", "379.107 tham số, 694 mẫu train, đối chiếu 4.656 ô dữ liệu", "F1 HEADER: 94,82%\nF1 VALUE: 96,15%"),
        ("Giao diện Preview & Cache Tự học", "Lưới Handsontable đa cấp, sửa ô trực tiếp, Hybrid Cache 2 tầng, Modal xác nhận và API an toàn.", "6 tầng header, 78 ô gộp, 3 bước quy trình khép kín", "16/16 UI TEST PASS\n3/3 TEST TỰ HỌC PASS"),
        ("Kiểm thử End-to-End & Bàn giao", "Kiểm thử tự động bằng Playwright, xây dựng kịch bản QA, tài liệu kỹ thuật và buổi Showcase nội bộ.", "12/12 ca kiểm thử E2E (Tuần 8-10), 100% kịch bản đạt yêu cầu", "MENTOR NGHIỆM THU\nĐẠT LOẠI XUẤT SẮC")
    ]
    for i, row in enumerate(products):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j); cell.text = val; cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else CARD_BG
            p = cell.text_frame.paragraphs[0]; p.font.size = Pt(11); p.font.color.rgb = SLATE_DARK
            if j == 0: p.font.bold = True
            if j == 3: p.font.bold = True; p.alignment = PP_ALIGN.CENTER; p.font.color.rgb = GREEN_ACCENT

    # Thẻ kết quả Showcase với Mentor Đào Đức Văn
    add_card(s14, Inches(0.8), Inches(4.9), Inches(11.73), Inches(1.8), "KẾT QUẢ ĐÁNH GIÁ TẠI BUỔI BÁO CÁO SHOWCASE VỚI MENTOR (16/10/2026)")
    tx = s14.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(11.3), Inches(1.2))
    tf = tx.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Cán bộ hướng dẫn Đào Đức Văn và nhóm phát triển eGov Solutions ghi nhận và đánh giá:"
    p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = NAVY_PRIMARY
    p_sc = tf.add_paragraph()
    p_sc.text = "1. Giải quyết trúng bài toán thực tế: Module giải quyết triệt để nút thắt nhập liệu thủ công với các bảng tính Excel phức tạp của ngành Tư pháp.\n" \
                "2. Tính độc lập & An toàn cao: Kiến trúc phân tầng tách biệt, không sửa đổi bảng cốt lõi eForm, có cơ chế bắt lỗi file rác và xác nhận hai bước chặt chẽ.\n" \
                "3. Khả năng áp dụng cao: Giao diện bảng tính trực quan, quen thuộc với cán bộ cơ sở; cơ chế Cache tự học giảm thiểu chi phí tài nguyên tính toán."
    p_sc.font.size = Pt(11.5); p_sc.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 15: PHẦN 3 - CÔNG NGHỆ VÀ CÔNG CỤ SỬ DỤNG
    # =========================================================================
    s15 = create_base_slide(prs, "CÁC KỸ NĂNG VÀ CÔNG CỤ KỸ THUẬT ĐÃ SỬ DỤNG", "PHẦN 3: NỘI DUNG & KẾT QUẢ", 15)
    tech_stacks = [
        ("BACKEND & NỀN TẢNG HỆ THỐNG",
         [("C# / .NET Framework 4.8", "Xây dựng dịch vụ ImportService, controller và luồng xử lý dữ liệu."),
          ("ASP.NET MVC 5 & Web API 2", "Tiếp nhận yêu cầu Multipart, điều phối API và render view."),
          ("Entity Framework 6", "Ánh xạ thực thể và lưu trữ an toàn vào cơ sở dữ liệu."),
          ("IIS / IIS Express", "Triển khai máy chủ web và cấu hình môi trường chạy ứng dụng.")]),
        ("TRÍ TUỆ NHÂN TẠO & PYTHON",
         [("Python 3.10+ / openpyxl", "Bóc tách cấu trúc workbook, ô gộp và ma trận bảng tính."),
          ("PyTorch 2.8.0 (CPU)", "Huấn luyện và triển khai mô hình học sâu Compact U-Net."),
          ("FastAPI & Pydantic", "Xây dựng microservice hiệu năng cao, thẩm định JSON 2.0."),
          ("Swagger / OpenAPI", "Tài liệu hóa và kiểm thử tương tác các dịch vụ API.")]),
        ("FRONTEND & TƯƠNG TÁC NGƯỜI DÙNG",
         [("Handsontable Grid", "Dựng lưới xem trước đa cấp, cuộn 2 chiều, chỉnh sửa trực tiếp."),
          ("JavaScript (ES6+) & jQuery", "Xử lý sự kiện giao diện, điều hướng DOM và gọi AJAX."),
          ("Backbone.js", "Quản lý trạng thái và mô hình dữ liệu trên hệ thống eForm BTP."),
          ("Bootstrap 3.4.1 & CSS3", "Định kiểu giao diện chuẩn công thái học phần mềm hành chính.")]),
        ("CSDL, BỘ NHỚ ĐỆM & CÔNG CỤ",
         [("MySQL 5.7 / Datamart", "Quản trị dữ liệu nghiệp vụ, viết Stored Procedure tổng hợp."),
          ("Redis Cache phân tán", "Tối ưu hóa hiệu năng mở biểu tổng hợp (>80% tốc độ)."),
          ("Playwright Test Framework", "Kiểm thử tự động toàn diện Frontend, Backend và End-to-End."),
          ("Git / GitLab & eTask", "Quản lý phiên bản mã nguồn, quy trình Merge Request và tiến độ.")])
    ]
    for i, (cat_title, cat_items) in enumerate(tech_stacks):
        left = Inches(0.8 + (i % 2) * 6.0)
        top = Inches(1.5 + (i // 2) * 2.8)
        add_card(s15, left, top, Inches(5.7), Inches(2.6), cat_title)
        tx = s15.shapes.add_textbox(left + Inches(0.15), top + Inches(0.55), Inches(5.4), Inches(1.9))
        tf = tx.text_frame; tf.word_wrap = True
        for tech, desc in cat_items:
            p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
            p.text = "• " + tech + ": "
            p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLUE_ACCENT
            p2 = tf.add_paragraph()
            p2.text = "  " + desc
            p2.font.size = Pt(10.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 16: PHẦN 4 - PHÂN TÍCH, ĐÁNH GIÁ VÀ ĐỀ XUẤT GIẢI PHÁP
    # =========================================================================
    s16 = create_base_slide(prs, "PHÂN TÍCH, ĐÁNH GIÁ VÀ ĐỀ XUẤT KỸ THUẬT", "PHẦN 4: PHÂN TÍCH & ĐÁNH GIÁ", 16)
    add_card(s16, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "NHẬN XÉT QUY TRÌNH & KHÓ KHĂN KỸ THUẬT")
    tx = s16.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    challenges = [
        ("Quy trình công việc doanh nghiệp:", "Quy trình làm việc tại DXP VN rất chuyên nghiệp, phân định rõ ràng giữa các bộ phận (BA, Dev, QA, DevOps). Mọi thay đổi mã nguồn bắt buộc phải qua Merge Request và kiểm thử kỹ lưỡng."),
        ("Khó khăn 1: Biểu mẫu đa dạng, phân cấp sâu:", "Các biểu mẫu Excel có cấu trúc biến thiên, ô gộp phức tạp dễ gây xô lệch cột. -> Giải pháp: Bóc tách ma trận hình học và phân loại theo họ bố cục."),
        ("Khó khăn 2: Xung đột DOM trên giao diện đa tab:", "Mở 2 báo cáo con cùng lúc bị ghi đè giao diện do trùng ID tĩnh. -> Giải pháp: Phân lập định danh bằng hậu tố tabSuffix (DocumentId)."),
        ("Khó khăn 3: Thất thoát dữ liệu khi nộp bổ sung:", "Quy trình gửi bổ sung bỏ sót ghi nhận vào fact_Note. -> Giải pháp: Tái cấu trúc backend ghi nhận bản ghi mới theo DocumentVersionId.")
    ]
    for h, b in challenges:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s16, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "LIÊN HỆ LÝ THUYẾT & KIẾN NGHỊ CẢI TIẾN")
    tx2 = s16.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    lessons = [
        ("Mối liên hệ giữa lý thuyết HUCE và thực tế:", "Kiến thức về Công nghệ phần mềm, CSDL quan hệ, Cấu trúc dữ liệu và Trí tuệ nhân tạo được đào tạo tại Khoa CNTT - HUCE đã giúp em nhanh chóng nắm bắt bản chất vấn đề, tiếp cận mã nguồn dự án lớn và tự xây dựng giải pháp học máy hoàn chỉnh."),
        ("Tư duy kiến trúc phòng thủ (Defensive Design):", "Trong hệ thống hành chính công, việc kiểm tra hợp lệ dữ liệu không thể chỉ dựa vào một phía. Cần kiểm soát chặt chẽ cả ở Client, Backend và CSDL."),
        ("Kiến nghị 1: Mở rộng Redis Cache đa tầng:", "Áp dụng cơ chế lưu đệm phân tán Redis cho toàn bộ các biểu mẫu báo cáo lớn của Bộ Tư pháp nhằm tối ưu tài nguyên máy chủ trong các kỳ cao điểm chốt số."),
        ("Kiến nghị 2: Tích hợp Module AI chính thức:", "Đưa Module AI Import Excel vào giai đoạn thử nghiệm có giám sát tại một số Sở Tư pháp lớn để thu thập thêm dữ liệu phản hồi trước khi triển khai diện rộng.")
    ]
    for h, b in lessons:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 17: PHẦN 5 - TỰ NHẬN XÉT VÀ ĐỊNH HƯỚNG BẢN THÂN
    # =========================================================================
    s17 = create_base_slide(prs, "TỰ NHẬN XÉT NĂNG LỰC VÀ ĐỊNH HƯỚNG NGHỀ NGHIỆP", "PHẦN 5: TỰ NHẬN XÉT & ĐỊNH HƯỚNG", 17)
    add_card(s17, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "TỰ ĐÁNH GIÁ NĂNG LỰC BẢN THÂN")
    tx = s17.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    self_eval = [
        ("Điểm mạnh nổi bật:", ""),
        ("• Khả năng tự học và nghiên cứu công nghệ mới:", "Chủ động tìm hiểu, hiện thực hóa thành công các công nghệ phức tạp (.NET MVC, Redis Cache, PyTorch, FastAPI, Handsontable) đáp ứng yêu cầu dự án."),
        ("• Tư duy giải quyết vấn đề hệ thống:", "Biết cách truy vết nguyên nhân gốc rễ (Root Cause Analysis) qua log, debug, gói tin mạng thay vì sửa chữa bề nổi."),
        ("• Tinh thần kỷ luật và trách nhiệm:", "Luôn bám sát tiến độ hàng ngày, tuân thủ quy chuẩn quản lý mã nguồn và hoàn thành 100% nhiệm vụ được giao."),
        ("Điểm cần tiếp tục hoàn thiện:", ""),
        ("• Kinh nghiệm hạ tầng Cloud Native & CI/CD:", "Cần trau dồi thêm về Docker, Kubernetes và các đường ống tự động hóa triển khai trên đám mây."),
        ("• Kỹ năng quản lý thời gian:", "Cần tối ưu hóa phân bổ thời gian khi đồng thời xử lý nhiều nhiệm vụ kỹ thuật phức tạp trong thời gian ngắn.")
    ]
    for h, b in self_eval:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        if not b:
            p.text = h; p.font.bold = True; p.font.size = Pt(13); p.font.color.rgb = NAVY_PRIMARY
        else:
            p.text = h; p.font.bold = True; p.font.size = Pt(11.5); p.font.color.rgb = BLUE_ACCENT
            p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    add_card(s17, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "KẾ HOẠCH HỌC TẬP & ĐỊNH HƯỚNG TƯƠNG LAI")
    tx2 = s17.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    career_plan = [
        ("Kế hoạch học tập ngắn hạn (2026 - 2027):", ""),
        ("• Hoàn thành Đồ án tốt nghiệp Đại học:", "Phát triển mở rộng đề tài Module AI Import Excel thành Đồ án tốt nghiệp chuyên ngành Khoa học máy tính dưới sự hướng dẫn của TS. Hoàng Nam Thắng, phấn đấu đạt kết quả Xuất sắc."),
        ("• Nâng cao trình độ ngoại ngữ & Chứng chỉ nghề:", "Tiếp tục nâng cao năng lực tiếng Anh chuyên ngành và ôn luyện các chứng chỉ kiến trúc phần mềm tiêu chuẩn."),
        ("Định hướng nghề nghiệp dài hạn:", ""),
        ("• Mục tiêu vị trí nghề nghiệp:", "Phấn đấu trở thành Kỹ sư phần mềm Full-Stack chuyên sâu (Senior Software Engineer) hoặc Kỹ sư AI ứng dụng (Applied AI Engineer)."),
        ("• Lĩnh vực trọng tâm cống hiến:", "Tập trung vào lĩnh vực phát triển các nền tảng Chính phủ số (eGov/GovTech) và Chuyển đổi số quốc gia, đóng góp năng lực kỹ thuật xây dựng hạ tầng số văn minh, hiện đại cho đất nước.")
    ]
    for h, b in career_plan:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        if not b:
            p.text = h; p.font.bold = True; p.font.size = Pt(13); p.font.color.rgb = NAVY_PRIMARY
        else:
            p.text = h; p.font.bold = True; p.font.size = Pt(11.5); p.font.color.rgb = BLUE_ACCENT
            p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 18: PHẦN 6 - KẾT LUẬN TOÀN DIỆN KỲ THỰC TẬP
    # =========================================================================
    s18 = create_base_slide(prs, "KẾT LUẬN TOÀN DIỆN VÀ BÀI HỌC KINH NGHIỆM", "PHẦN 6: KẾT LUẬN & KIẾN NGHỊ", 18)
    add_card(s18, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2), "TỔNG KẾT KẾT QUẢ KỲ THỰC TẬP 11 TUẦN")
    tx = s18.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf = tx.text_frame; tf.word_wrap = True
    conclusions = [
        ("Hoàn thành 100% mục tiêu đào tạo:", "Đáp ứng đầy đủ và vượt mức các chuẩn đầu ra (CLO 1 - CLO 4) của học phần Thực tập tốt nghiệp do Trường ĐH Xây dựng Hà Nội quy định."),
        ("Đóng góp thực tế cho Dự án Quốc gia:", "Trực tiếp xử lý thành công hàng loạt bài toán nghiệp vụ phức tạp của Hệ thống eForm BTP (từ cấp Cục đến 3.321 xã trên toàn quốc), giúp hệ thống vận hành ổn định, chính xác và mượt mà hơn."),
        ("Hoàn thiện sản phẩm nghiên cứu cá nhân:", "Xây dựng trọn vẹn Module AI Import Excel với đầy đủ kiến trúc phân tầng, lưới xem trước đa cấp, cơ chế Cache tự học và bộ kiểm thử tự động toàn diện đạt 100% tỷ lệ thành công."),
        ("Được doanh nghiệp nghiệm thu Xuất sắc:", "Toàn bộ các sản phẩm kỹ thuật và báo cáo công tác đều được Cán bộ hướng dẫn Đào Đức Văn và Ban lãnh đạo công ty đánh giá rất cao.")
    ]
    for h, b in conclusions:
        p1 = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = NAVY_PRIMARY
        p2 = tf.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    add_card(s18, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2), "BÀI HỌC KINH NGHIỆM ĐẮT GIÁ")
    tx2 = s18.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.3), Inches(4.3))
    tf2 = tx2.text_frame; tf2.word_wrap = True
    lessons_learned = [
        ("Hiểu sâu nghiệp vụ trước khi viết mã:", "Trong hệ thống phần mềm hành chính công vụ, nghiệp vụ luôn đi trước công nghệ. Cần đọc hiểu tường tận quy định pháp lý và quy trình thực tế trước khi can thiệp vào mã nguồn."),
        ("Tư duy thiết kế an toàn và phòng thủ:", "Không bao giờ tin tưởng tuyệt đối vào dữ liệu người dùng hay kết quả của mô hình AI. Cần trang bị các lớp kiểm tra hợp lệ độc lập ở tầng ứng dụng và cơ sở dữ liệu."),
        ("Quy trình kiểm thử tự động là sống còn:", "Việc áp dụng các bài kiểm thử tự động (Playwright) giúp phát hiện sớm các lỗi hồi quy và đảm bảo sự an tâm tuyệt đối khi nâng cấp hoặc vá lỗi hệ thống lớn."),
        ("Sự phối hợp và trao đổi cởi mở trong nhóm:", "Thường xuyên trao đổi với Mentor và các kỹ sư giàu kinh nghiệm giúp tiết kiệm thời gian mò mẫm, tìm ra giải pháp tối ưu và phát triển bản thân nhanh chóng.")
    ]
    for h, b in lessons_learned:
        p1 = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p1.text = "• " + h; p1.font.bold = True; p1.font.size = Pt(12); p1.font.color.rgb = BLUE_ACCENT
        p2 = tf2.add_paragraph(); p2.text = "  " + b; p2.font.size = Pt(11.5); p2.font.color.rgb = SLATE_DARK

    # =========================================================================
    # SLIDE 19: PHIÊN HỎI ĐÁP & KẾT THÚC
    # =========================================================================
    s19 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_transition(s19)
    bg19 = s19.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg19.fill.solid(); bg19.fill.fore_color.rgb = NAVY_PRIMARY; bg19.line.fill.background()

    if os.path.exists(LOGO_HUCE):
        s19.shapes.add_picture(LOGO_HUCE, Inches(5.9), Inches(1.2), width=Inches(1.5))

    tx_end = s19.shapes.add_textbox(Inches(1.0), Inches(2.9), Inches(11.33), Inches(3.0))
    tf_end = tx_end.text_frame
    p_e1 = tf_end.paragraphs[0]
    p_e1.text = "TRÂN TRỌNG CẢM ƠN QUÝ THẦY CÔ VÀ HỘI ĐỒNG!"
    p_e1.font.name = "Arial"; p_e1.font.size = Pt(26); p_e1.font.bold = True
    p_e1.font.color.rgb = WHITE; p_e1.alignment = PP_ALIGN.CENTER

    p_e2 = tf_end.add_paragraph()
    p_e2.text = "Kính chúc Quý Thầy Cô sức khỏe, hạnh phúc và thành công trong sự nghiệp giáo dục!"
    p_e2.font.name = "Arial"; p_e2.font.size = Pt(15); p_e2.font.italic = True
    p_e2.font.color.rgb = RGBColor(186, 230, 253); p_e2.alignment = PP_ALIGN.CENTER

    p_e3 = tf_end.add_paragraph()
    p_e3.text = "\nEM XIN LẮNG NGHE VÀ TIẾP THU CÁC Ý KIẾN ĐÓNG GÓP, CÂU HỎI TỪ HỘI ĐỒNG (Q&A)"
    p_e3.font.name = "Arial"; p_e3.font.size = Pt(16); p_e3.font.bold = True
    p_e3.font.color.rgb = RGBColor(56, 189, 248); p_e3.alignment = PP_ALIGN.CENTER

    out_file1 = "Báo cáo thực tập tốt nghiệp Tuần 1 - 11 (HUCE).pptx"
    prs.save(out_file1)
    print(f"Saved {out_file1} successfully with {len(prs.slides)} slides!")

if __name__ == '__main__':
    build_presentation()
