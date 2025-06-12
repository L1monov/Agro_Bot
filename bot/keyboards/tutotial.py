from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder

def get_next_button(step: int):
    """
    step: следующий номер шага (2 или 3).
    Для последнего шага можно передавать None и возвращать пустую клавиатуру.
    """
    kb = InlineKeyboardBuilder()
    if step:
        kb.row(
            InlineKeyboardButton(
                text="Далее",
                callback_data=f"tutorial_step:{step}"
            )
        )
    return kb.as_markup()