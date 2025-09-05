from aiogram.fsm.state import State, StatesGroup

class QuestionStates(StatesGroup):
    """States for question submission flow"""
    waiting_for_category = State()
    waiting_for_question = State()

class AnswerStates(StatesGroup):
    """States for answer submission flow"""
    waiting_for_answer = State()

class AdminStates(StatesGroup):
    """States for admin operations"""
    waiting_for_confirmation = State()