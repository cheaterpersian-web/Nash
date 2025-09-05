import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from database import Database
from keyboards import (
    get_main_menu_keyboard, get_category_keyboard, get_questions_keyboard,
    get_question_detail_keyboard, get_answers_keyboard, get_answer_detail_keyboard,
    get_top_answers_keyboard, get_admin_keyboard, get_cancel_keyboard
)
from states import QuestionStates, AnswerStates, AdminStates
from config import TEXTS, ADMIN_IDS, QUESTIONS_PER_PAGE, ANSWERS_PER_PAGE

logger = logging.getLogger(__name__)
router = Router()
db = Database()

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    user_id = await db.add_user(message.from_user.id)
    logger.info(f"User {message.from_user.id} started the bot")
    
    await message.answer(
        TEXTS['welcome'],
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Handle /admin command"""
    if not is_admin(message.from_user.id):
        await message.answer(TEXTS['access_denied'])
        return
    
    await state.clear()
    await message.answer(
        TEXTS['admin_menu'],
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle main menu callback"""
    await state.clear()
    await callback.message.edit_text(
        TEXTS['main_menu'],
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "ask_question")
async def callback_ask_question(callback: CallbackQuery, state: FSMContext):
    """Handle ask question callback"""
    await state.set_state(QuestionStates.waiting_for_category)
    await callback.message.edit_text(
        TEXTS['select_category'],
        reply_markup=get_category_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("category_"))
async def callback_category_selected(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    category = callback.data.split("_")[1]
    await state.update_data(category=category)
    await state.set_state(QuestionStates.waiting_for_question)
    
    await callback.message.edit_text(
        TEXTS['enter_question'],
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(QuestionStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Process question text"""
    data = await state.get_data()
    category = data.get('category')
    
    if not category or len(message.text.strip()) < 10:
        await message.answer(
            "⚠️ لطفاً سوال خود را کامل بنویسید (حداقل 10 کاراکتر).",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = await db.add_user(message.from_user.id)
    question_id = await db.add_question(user_id, category, message.text.strip())
    
    await state.clear()
    await message.answer(
        TEXTS['question_saved'],
        reply_markup=get_main_menu_keyboard()
    )
    
    logger.info(f"Question {question_id} added by user {message.from_user.id}")

@router.callback_query(F.data == "view_questions")
async def callback_view_questions(callback: CallbackQuery, state: FSMContext):
    """Handle view questions callback"""
    await state.clear()
    questions = await db.get_questions(page=0, limit=QUESTIONS_PER_PAGE)
    
    if not questions:
        await callback.message.edit_text(
            TEXTS['no_questions'],
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Check if there are more questions
    total_questions = await db.get_question_count()
    has_next = len(questions) == QUESTIONS_PER_PAGE and total_questions > QUESTIONS_PER_PAGE
    
    text = "📋 سوالات اخیر:\n\n"
    for i, question in enumerate(questions, 1):
        question_id, category, question_text, created_at, answer_count = question
        category_emoji = TEXTS['categories'].get(category, "🎭")
        text += f"{i}. {category_emoji} {question_text[:100]}{'...' if len(question_text) > 100 else ''}\n"
        text += f"   📅 {created_at} | 💬 {answer_count} پاسخ\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_questions_keyboard(questions, page=0, has_next=has_next)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("questions_page_"))
async def callback_questions_page(callback: CallbackQuery, state: FSMContext):
    """Handle questions pagination"""
    page = int(callback.data.split("_")[2])
    questions = await db.get_questions(page=page, limit=QUESTIONS_PER_PAGE)
    
    if not questions:
        await callback.answer("❌ صفحه‌ای یافت نشد.")
        return
    
    # Check if there are more questions
    total_questions = await db.get_question_count()
    has_next = len(questions) == QUESTIONS_PER_PAGE and total_questions > (page + 1) * QUESTIONS_PER_PAGE
    
    text = f"📋 سوالات اخیر (صفحه {page + 1}):\n\n"
    for i, question in enumerate(questions, 1):
        question_id, category, question_text, created_at, answer_count = question
        category_emoji = TEXTS['categories'].get(category, "🎭")
        text += f"{i}. {category_emoji} {question_text[:100]}{'...' if len(question_text) > 100 else ''}\n"
        text += f"   📅 {created_at} | 💬 {answer_count} پاسخ\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_questions_keyboard(questions, page=page, has_next=has_next)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("question_"))
async def callback_question_detail(callback: CallbackQuery, state: FSMContext):
    """Handle question detail view"""
    question_id = int(callback.data.split("_")[1])
    question = await db.get_question_by_id(question_id)
    
    if not question:
        await callback.answer("❌ سوال یافت نشد.")
        return
    
    question_id, category, text, created_at = question
    category_emoji = TEXTS['categories'].get(category, "🎭")
    
    text_display = f"❓ سوال:\n{category_emoji} {text}\n\n📅 تاریخ: {created_at}"
    
    is_admin_user = is_admin(callback.from_user.id)
    await callback.message.edit_text(
        text_display,
        reply_markup=get_question_detail_keyboard(question_id, is_admin_user)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("answer_question_"))
async def callback_answer_question(callback: CallbackQuery, state: FSMContext):
    """Handle answer question callback"""
    question_id = int(callback.data.split("_")[2])
    await state.update_data(question_id=question_id)
    await state.set_state(AnswerStates.waiting_for_answer)
    
    await callback.message.edit_text(
        TEXTS['enter_answer'],
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(AnswerStates.waiting_for_answer)
async def process_answer(message: Message, state: FSMContext):
    """Process answer text"""
    data = await state.get_data()
    question_id = data.get('question_id')
    
    if not question_id or len(message.text.strip()) < 5:
        await message.answer(
            "⚠️ لطفاً پاسخ خود را کامل بنویسید (حداقل 5 کاراکتر).",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = await db.add_user(message.from_user.id)
    answer_id = await db.add_answer(question_id, user_id, message.text.strip())
    
    await state.clear()
    await message.answer(
        TEXTS['answer_saved'],
        reply_markup=get_main_menu_keyboard()
    )
    
    logger.info(f"Answer {answer_id} added to question {question_id} by user {message.from_user.id}")

@router.callback_query(F.data.startswith("view_answers_"))
async def callback_view_answers(callback: CallbackQuery, state: FSMContext):
    """Handle view answers callback"""
    question_id = int(callback.data.split("_")[2])
    answers = await db.get_answers(question_id, page=0, limit=ANSWERS_PER_PAGE)
    
    if not answers:
        await callback.answer("❌ هیچ پاسخی یافت نشد.")
        return
    
    # Check if there are more answers
    total_answers = await db.get_answer_count(question_id)
    has_next = len(answers) == ANSWERS_PER_PAGE and total_answers > ANSWERS_PER_PAGE
    
    text = f"💬 پاسخ‌ها:\n\n"
    for i, answer in enumerate(answers, 1):
        answer_id, answer_text, created_at, votes, is_pinned = answer
        pin_icon = "📌 " if is_pinned else ""
        vote_icon = "👍" if votes > 0 else "👎" if votes < 0 else "⚪"
        text += f"{i}. {pin_icon}{vote_icon} {answer_text[:80]}{'...' if len(answer_text) > 80 else ''}\n"
        text += f"   📅 {created_at} | {votes} نظر\n\n"
    
    is_admin_user = is_admin(callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=get_answers_keyboard(answers, question_id, page=0, has_next=has_next, is_admin=is_admin_user)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("answers_page_"))
async def callback_answers_page(callback: CallbackQuery, state: FSMContext):
    """Handle answers pagination"""
    parts = callback.data.split("_")
    question_id = int(parts[2])
    page = int(parts[3])
    
    answers = await db.get_answers(question_id, page=page, limit=ANSWERS_PER_PAGE)
    
    if not answers:
        await callback.answer("❌ صفحه‌ای یافت نشد.")
        return
    
    # Check if there are more answers
    total_answers = await db.get_answer_count(question_id)
    has_next = len(answers) == ANSWERS_PER_PAGE and total_answers > (page + 1) * ANSWERS_PER_PAGE
    
    text = f"💬 پاسخ‌ها (صفحه {page + 1}):\n\n"
    for i, answer in enumerate(answers, 1):
        answer_id, answer_text, created_at, votes, is_pinned = answer
        pin_icon = "📌 " if is_pinned else ""
        vote_icon = "👍" if votes > 0 else "👎" if votes < 0 else "⚪"
        text += f"{i}. {pin_icon}{vote_icon} {answer_text[:80]}{'...' if len(answer_text) > 80 else ''}\n"
        text += f"   📅 {created_at} | {votes} نظر\n\n"
    
    is_admin_user = is_admin(callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=get_answers_keyboard(answers, question_id, page=page, has_next=has_next, is_admin=is_admin_user)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("answer_detail_"))
async def callback_answer_detail(callback: CallbackQuery, state: FSMContext):
    """Handle answer detail view"""
    answer_id = int(callback.data.split("_")[2])
    
    # Get answer details (simplified for now)
    # In a real implementation, you'd fetch the full answer details from database
    
    text = f"💬 پاسخ:\n\n[پاسخ با شناسه {answer_id}]\n\n👍 می‌توانید نظر خود را ثبت کنید:"
    
    is_admin_user = is_admin(callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=get_answer_detail_keyboard(answer_id, 0, is_admin_user)  # question_id=0 for now
    )
    await callback.answer()

@router.callback_query(F.data.startswith("vote_"))
async def callback_vote(callback: CallbackQuery, state: FSMContext):
    """Handle voting on answers"""
    parts = callback.data.split("_")
    answer_id = int(parts[1])
    vote_value = int(parts[2])
    
    user_id = await db.add_user(callback.from_user.id)
    success = await db.vote_answer(answer_id, user_id, vote_value)
    
    if success:
        await callback.answer(TEXTS['vote_success'])
    else:
        await callback.answer(TEXTS['already_voted'])
    
    # Refresh the answer detail view
    await callback_answer_detail(callback, state)

@router.callback_query(F.data == "top_answers")
async def callback_top_answers(callback: CallbackQuery, state: FSMContext):
    """Handle top answers callback"""
    await state.clear()
    answers = await db.get_top_answers(page=0, limit=ANSWERS_PER_PAGE)
    
    if not answers:
        await callback.message.edit_text(
            "❌ هیچ پاسخی یافت نشد.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    text = "⭐ محبوب‌ترین پاسخ‌ها:\n\n"
    for i, answer in enumerate(answers, 1):
        answer_id, answer_text, votes, created_at, question_text, category = answer
        category_emoji = TEXTS['categories'].get(category, "🎭")
        vote_icon = "👍" if votes > 0 else "👎" if votes < 0 else "⚪"
        text += f"{i}. {vote_icon} {answer_text[:60]}{'...' if len(answer_text) > 60 else ''}\n"
        text += f"   {category_emoji} {question_text[:40]}{'...' if len(question_text) > 40 else ''}\n"
        text += f"   📅 {created_at} | {votes} نظر\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_top_answers_keyboard(answers, page=0, has_next=False)  # Simplified for now
    )
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Handle cancel callback"""
    await state.clear()
    await callback.message.edit_text(
        TEXTS['main_menu'],
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

# Admin handlers
@router.callback_query(F.data.startswith("delete_question_"))
async def callback_delete_question(callback: CallbackQuery, state: FSMContext):
    """Handle delete question (admin only)"""
    if not is_admin(callback.from_user.id):
        await callback.answer(TEXTS['access_denied'])
        return
    
    question_id = int(callback.data.split("_")[2])
    success = await db.delete_question(question_id)
    
    if success:
        await callback.answer("✅ سوال حذف شد.")
        await callback_main_menu(callback, state)
    else:
        await callback.answer("❌ خطا در حذف سوال.")

@router.callback_query(F.data.startswith("delete_answer_"))
async def callback_delete_answer(callback: CallbackQuery, state: FSMContext):
    """Handle delete answer (admin only)"""
    if not is_admin(callback.from_user.id):
        await callback.answer(TEXTS['access_denied'])
        return
    
    answer_id = int(callback.data.split("_")[2])
    success = await db.delete_answer(answer_id)
    
    if success:
        await callback.answer("✅ پاسخ حذف شد.")
    else:
        await callback.answer("❌ خطا در حذف پاسخ.")

@router.callback_query(F.data.startswith("pin_answer_"))
async def callback_pin_answer(callback: CallbackQuery, state: FSMContext):
    """Handle pin answer (admin only)"""
    if not is_admin(callback.from_user.id):
        await callback.answer(TEXTS['access_denied'])
        return
    
    answer_id = int(callback.data.split("_")[2])
    success = await db.pin_answer(answer_id, True)
    
    if success:
        await callback.answer("✅ پاسخ سنجاق شد.")
    else:
        await callback.answer("❌ خطا در سنجاق کردن پاسخ.")

# Error handler
@router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """Handle unknown messages"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "لطفاً از منوی زیر استفاده کنید:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(
            "⚠️ لطفاً عملیات قبلی را تکمیل کنید یا لغو کنید.",
            reply_markup=get_cancel_keyboard()
        )