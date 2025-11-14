from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


def get_main_keyboard():
    """
    Возвращает основную клавиатуру с тремя кнопками:
    - Проверить URL
    - Пройти тест
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(CallbackButton(text="Проверить URL", payload="check_url"))
    builder.row(CallbackButton(text="Пройти тест", payload="start_test"))
    return builder.as_markup()
    
def segment_keyboard():  
    builder = InlineKeyboardBuilder()
    
    builder.row(CallbackButton(text="Средняя школа", payload="middle_school"))
    builder.row(CallbackButton(text="Старшая школа", payload="senior_school"))
    builder.row(CallbackButton(text="Студенты или молодые специалисты", payload="students"))
    builder.row(CallbackButton(text="Миллениалы", payload="millennials"))
    builder.row(CallbackButton(text="Пенсионеры", payload="retirees"))
    return builder.as_markup()
    
def answer_keyboard():
    
    """клавиатура с номерами ответов на тест"""
    
    builder = InlineKeyboardBuilder()
    builder.row(
    CallbackButton(text="1", payload="answer_1"),
    CallbackButton(text="2", payload="answer_2"),
    CallbackButton(text="3", payload="answer_3"),
    CallbackButton(text="4", payload="answer_4")
    )
    return builder.as_markup()

    
