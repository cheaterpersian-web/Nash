import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')

# Persian text constants
TEXTS = {
    'welcome': '🤖 به ربات سوال و جواب ناشناس خوش آمدید!\n\n'
               'در این ربات می‌توانید سوالات خود را به صورت ناشناس بپرسید و به سوالات دیگران پاسخ دهید.',
    
    'main_menu': '📋 منوی اصلی',
    
    'ask_question': '✍️ ارسال سوال ناشناس',
    'view_questions': '👀 دیدن سوالات دیگران',
    'answer_questions': '💬 پاسخ دادن به سوالات',
    'top_answers': '⭐ محبوب‌ترین پاسخ‌ها',
    
    'select_category': '📂 لطفاً دسته‌بندی سوال خود را انتخاب کنید:',
    'enter_question': '✍️ لطفاً سوال خود را بنویسید:',
    'question_saved': '✅ سوال شما با موفقیت ثبت شد!',
    
    'no_questions': '❌ هیچ سوالی یافت نشد.',
    'select_question': '❓ لطفاً سوالی را برای پاسخ انتخاب کنید:',
    'enter_answer': '💭 لطفاً پاسخ خود را بنویسید:',
    'answer_saved': '✅ پاسخ شما با موفقیت ثبت شد!',
    
    'vote_success': '✅ نظر شما ثبت شد!',
    'already_voted': '⚠️ شما قبلاً به این پاسخ نظر داده‌اید.',
    
    'admin_menu': '🔧 پنل مدیریت',
    'delete_question': '🗑️ حذف سوال',
    'delete_answer': '🗑️ حذف پاسخ',
    'pin_answer': '📌 سنجاق کردن پاسخ',
    'unpin_answer': '📌 برداشتن سنجاق',
    
    'error': '❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.',
    'invalid_input': '⚠️ ورودی نامعتبر است.',
    'access_denied': '🚫 دسترسی غیرمجاز.',
    
    'categories': {
        'love': '❤️ روابط عاطفی',
        'work': '💼 کار و شغل',
        'education': '📚 تحصیل',
        'health': '🩺 سلامت',
        'other': '🎭 سایر'
    }
}

# Pagination settings
QUESTIONS_PER_PAGE = 5
ANSWERS_PER_PAGE = 10