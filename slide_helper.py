import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

# Màu sắc chủ đạo (Hệ màu chuyên nghiệp cho Báo cáo ĐH Xây dựng Hà Nội & Chính phủ số eGov)
NAVY_PRIMARY = RGBColor(10, 37, 64)       # Xanh Navy đậm chủ đạo (#0A2540)
BLUE_ACCENT = RGBColor(0, 102, 178)       # Xanh công nghệ eGov (#0066B2)
SLATE_DARK = RGBColor(30, 41, 59)         # Xám đậm chữ chính (#1E293B)
SLATE_MUTED = RGBColor(100, 116, 139)     # Xám phụ chú (#64748B)
BG_LIGHT = RGBColor(248, 250, 252)        # Nền sáng thanh lịch (#F8FAFC)
WHITE = RGBColor(255, 255, 255)           # Trắng tinh (#FFFFFF)
CARD_BG = RGBColor(241, 245, 249)         # Nền thẻ (#F1F5F9)
BORDER_COLOR = RGBColor(203, 213, 225)    # Viền nhạt (#CBD5E1)
GREEN_ACCENT = RGBColor(22, 101, 52)      # Xanh lá kết quả tốt (#166534)
RED_ACCENT = RGBColor(153, 27, 27)        # Đỏ nhấn (#991B1B)

LOGO_HUCE = os.path.abspath("huce_logo.png")

def add_slide_transition(slide):
    """Thêm hiệu ứng chuyển trang mượt mà (Fade transition) vào slide XML"""
    trans = parse_xml('<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:fade/></p:transition>')
    slide._element.append(trans)

def create_base_slide(prs, title_text, section_text=None, slide_num=None):
    """Tạo slide nội dung chuẩn với thanh tiêu đề, logo HUCE, footer và hiệu ứng chuyển trang"""
    slide = prs.slides.add_slide(prs.slide_layouts[6]) # blank layout
    add_slide_transition(slide)

    # Nền slide sáng
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_LIGHT
    bg.line.fill.background()

    # Dải màu đầu trang (Header bar)
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.1))
    header.fill.solid()
    header.fill.fore_color.rgb = NAVY_PRIMARY
    header.line.fill.background()

    # Logo HUCE nhỏ ở góc phải header
    if os.path.exists(LOGO_HUCE):
        slide.shapes.add_picture(LOGO_HUCE, Inches(12.2), Inches(0.12), width=Inches(0.85))

    # Tên phân mục nhỏ
    if section_text:
        tx_sec = slide.shapes.add_textbox(Inches(0.8), Inches(0.15), Inches(11.0), Inches(0.3))
        tf_sec = tx_sec.text_frame
        tf_sec.word_wrap = True
        p_sec = tf_sec.paragraphs[0]
        p_sec.text = section_text.upper()
        p_sec.font.name = "Arial"
        p_sec.font.size = Pt(11)
        p_sec.font.bold = True
        p_sec.font.color.rgb = RGBColor(56, 189, 248) # Xanh dương sáng

    # Tiêu đề slide
    tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.0), Inches(0.55))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Arial"
    p_title.font.size = Pt(20)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE

    # Footer chân trang
    line_footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.05), Inches(11.73), Inches(0.02))
    line_footer.fill.solid()
    line_footer.fill.fore_color.rgb = BORDER_COLOR
    line_footer.line.fill.background()

    tx_footer = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(10.0), Inches(0.3))
    tf_footer = tx_footer.text_frame
    p_foot = tf_footer.paragraphs[0]
    p_foot.text = "Trường ĐH Xây dựng Hà Nội | Khoa CNTT - Báo cáo Thực tập tốt nghiệp | SV: Trần Văn Hoàng - 0034467"
    p_foot.font.name = "Arial"
    p_foot.font.size = Pt(10)
    p_foot.font.color.rgb = SLATE_MUTED

    if slide_num:
        tx_num = slide.shapes.add_textbox(Inches(11.5), Inches(7.1), Inches(1.0), Inches(0.3))
        tf_num = tx_num.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.text = str(slide_num)
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.name = "Arial"
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = NAVY_PRIMARY

    return slide

def add_card(slide, left, top, width, height, title=None, bg_color=CARD_BG, border_color=BORDER_COLOR):
    """Tạo một thẻ khối nội dung với bo viền chuyên nghiệp"""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
    else:
        card.line.fill.background()

    if title:
        tx = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.12), width - Inches(0.3), Inches(0.4))
        p = tx.text_frame.paragraphs[0]
        p.text = title
        p.font.name = "Arial"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY

    return card

def create_module_base_slide(prs, title_text, section_text=None, slide_num=None):
    """Tạo slide nội dung chuẩn cho Báo cáo Chuyên đề Module Import Excel"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_transition(slide)

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_LIGHT
    bg.line.fill.background()

    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.1))
    header.fill.solid()
    header.fill.fore_color.rgb = NAVY_PRIMARY
    header.line.fill.background()

    if os.path.exists(LOGO_HUCE):
        slide.shapes.add_picture(LOGO_HUCE, Inches(12.2), Inches(0.12), width=Inches(0.85))

    if section_text:
        tx_sec = slide.shapes.add_textbox(Inches(0.8), Inches(0.15), Inches(11.0), Inches(0.3))
        tf_sec = tx_sec.text_frame
        tf_sec.word_wrap = True
        p_sec = tf_sec.paragraphs[0]
        p_sec.text = section_text.upper()
        p_sec.font.name = "Arial"
        p_sec.font.size = Pt(11)
        p_sec.font.bold = True
        p_sec.font.color.rgb = RGBColor(56, 189, 248)

    tx_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.0), Inches(0.55))
    tf_title = tx_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Arial"
    p_title.font.size = Pt(20)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE

    line_footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.05), Inches(11.73), Inches(0.02))
    line_footer.fill.solid()
    line_footer.fill.fore_color.rgb = BORDER_COLOR
    line_footer.line.fill.background()

    tx_footer = slide.shapes.add_textbox(Inches(0.8), Inches(7.1), Inches(10.0), Inches(0.3))
    tf_footer = tx_footer.text_frame
    p_foot = tf_footer.paragraphs[0]
    p_foot.text = "Trường ĐH Xây dựng Hà Nội | Chuyên đề: Module Import Excel AI - Hệ thống eForm BTP | SV: Trần Văn Hoàng - 0034467"
    p_foot.font.name = "Arial"
    p_foot.font.size = Pt(10)
    p_foot.font.color.rgb = SLATE_MUTED

    if slide_num:
        tx_num = slide.shapes.add_textbox(Inches(11.5), Inches(7.1), Inches(1.0), Inches(0.3))
        tf_num = tx_num.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.text = str(slide_num)
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.name = "Arial"
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = NAVY_PRIMARY

    return slide

def add_image_card(slide, left, top, width, height, image_path, title=None, caption=None):
    """Tạo một thẻ chứa hình ảnh minh chứng với viền trang nhã và chú thích chân thực"""
    card = add_card(slide, left, top, width, height, title)
    if os.path.exists(image_path):
        top_offset = Inches(0.5) if title else Inches(0.15)
        bottom_offset = Inches(0.4) if caption else Inches(0.15)
        avail_w = width - Inches(0.3)
        avail_h = height - top_offset - bottom_offset
        
        # Thêm ảnh căn chỉnh tỷ lệ
        pic = slide.shapes.add_picture(image_path, left + Inches(0.15), top + top_offset)
        # Scale to fit inside available box
        w_ratio = avail_w / pic.width
        h_ratio = avail_h / pic.height
        scale = min(w_ratio, h_ratio)
        pic.width = int(pic.width * scale)
        pic.height = int(pic.height * scale)
        # Căn giữa trong thẻ
        pic.left = int(left + (width - pic.width) / 2)
        pic.top = int(top + top_offset + (avail_h - pic.height) / 2)

    if caption:
        tx = slide.shapes.add_textbox(left + Inches(0.15), top + height - Inches(0.42), width - Inches(0.3), Inches(0.35))
        p = tx.text_frame.paragraphs[0]
        p.text = caption
        p.font.name = "Arial"
        p.font.size = Pt(9.5)
        p.font.italic = True
        p.font.color.rgb = SLATE_MUTED
        p.alignment = PP_ALIGN.CENTER

    return card

print("Module helper initialized successfully!")
