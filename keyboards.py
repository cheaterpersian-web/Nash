from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TEXTS

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard with Persian buttons"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="✍️ ارسال سوال ناشناس",
        callback_data="ask_question"
    ))
    builder.add(InlineKeyboardButton(
        text="👀 دیدن سوالات دیگران",
        callback_data="view_questions"
    ))
    builder.add(InlineKeyboardButton(
        text="💬 پاسخ دادن به سوالات",
        callback_data="answer_questions"
    ))
    builder.add(InlineKeyboardButton(
        text="⭐ محبوب‌ترین پاسخ‌ها",
        callback_data="top_answers"
    ))
    
    builder.adjust(1)  # One button per row
    return builder.as_markup()

def get_category_keyboard() -> InlineKeyboardMarkup:
    """Create category selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    categories = TEXTS['categories']
    for key, text in categories.items():
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"category_{key}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت به منوی اصلی",
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_questions_keyboard(questions: list, page: int = 0, has_next: bool = False) -> InlineKeyboardMarkup:
    """Create questions list keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    for question in questions:
        question_id, category, text, created_at, answer_count = question
        # Truncate long questions
        display_text = text[:50] + "..." if len(text) > 50 else text
        button_text = f"❓ {display_text} ({answer_count} پاسخ)"
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"question_{question_id}"
        ))
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ قبلی",
            callback_data=f"questions_page_{page-1}"
        ))
    
    if has_next:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ بعدی",
            callback_data=f"questions_page_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت به منوی اصلی",
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_question_detail_keyboard(question_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create keyboard for question detail view"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="💬 پاسخ دادن",
        callback_data=f"answer_question_{question_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="👀 دیدن پاسخ‌ها",
        callback_data=f"view_answers_{question_id}"
    ))
    
    if is_admin:
        builder.add(InlineKeyboardButton(
            text="🗑️ حذف سوال",
            callback_data=f"delete_question_{question_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="view_questions"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_answers_keyboard(answers: list, question_id: int, page: int = 0, has_next: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create answers list keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    for answer in answers:
        answer_id, text, created_at, votes, is_pinned = answer
        # Truncate long answers
        display_text = text[:40] + "..." if len(text) > 40 else text
        pin_icon = "📌 " if is_pinned else ""
        vote_icon = "👍" if votes > 0 else "👎" if votes < 0 else "⚪"
        button_text = f"{pin_icon}{vote_icon} {display_text} ({votes})"
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"answer_detail_{answer_id}"
        ))
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ قبلی",
            callback_data=f"answers_page_{question_id}_{page-1}"
        ))
    
    if has_next:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ بعدی",
            callback_data=f"answers_page_{question_id}_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.add(InlineKeyboardButton(
        text="💬 پاسخ جدید",
        callback_data=f"answer_question_{question_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data=f"question_{question_id}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_answer_detail_keyboard(answer_id: int, question_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Create keyboard for answer detail view"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="👍 موافقم",
        callback_data=f"vote_{answer_id}_1"
    ))
    builder.add(InlineKeyboardButton(
        text="👎 مخالفم",
        callback_data=f"vote_{answer_id}_-1"
    ))
    
    if is_admin:
        builder.add(InlineKeyboardButton(
            text="📌 سنجاق کردن",
            callback_data=f"pin_answer_{answer_id}"
        ))
        builder.add(InlineKeyboardButton(
            text="🗑️ حذف پاسخ",
            callback_data=f"delete_answer_{answer_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data=f"view_answers_{question_id}"
    ))
    
    builder.adjust(2, 1)  # Two buttons in first row, one in second
    return builder.as_markup()

def get_top_answers_keyboard(answers: list, page: int = 0, has_next: bool = False) -> InlineKeyboardMarkup:
    """Create top answers keyboard with pagination"""
    builder = InlineKeyboardBuilder()
    
    for answer in answers:
        answer_id, text, votes, created_at, question_text, category = answer
        # Truncate long answers
        display_text = text[:40] + "..." if len(text) > 40 else text
        vote_icon = "👍" if votes > 0 else "👎" if votes < 0 else "⚪"
        button_text = f"{vote_icon} {display_text} ({votes})"
        
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"top_answer_detail_{answer_id}"
        ))
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ قبلی",
            callback_data=f"top_answers_page_{page-1}"
        ))
    
    if has_next:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ بعدی",
            callback_data=f"top_answers_page_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت به منوی اصلی",
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="📊 آمار کلی",
        callback_data="admin_stats"
    ))
    builder.add(InlineKeyboardButton(
        text="🗑️ مدیریت محتوا",
        callback_data="admin_content"
    ))
    builder.add(InlineKeyboardButton(
        text="🔙 بازگشت به منوی اصلی",
        callback_data="main_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Create cancel keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="❌ لغو",
        callback_data="cancel"
    ))
    
    return builder.as_markup()