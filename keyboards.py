from aiogram.types import Message, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class ClassRoomsActionsCallback(CallbackData, prefix="ClassRoomsActions"):
    action: str # view_all/create

class ViewClassRoomsCallback(CallbackData, prefix="ViewClassRooms"):
    class_number: int
    purpose: str #view_classrooms/view_schedule


class ViewClassRoomCallback(CallbackData, prefix="ViewClassRoom"):
    class_number: int
    class_letter: str
    purpose: str #view_classrooms/view_schedule
    is_back: bool = False


class ClassRoomActionCallback(CallbackData, prefix="ClassRoomAction"):
    action: str #generate_qr_code/edit/delete/back and сonfirm_delete/cancel_delete
    class_number: int
    class_letter: str


class ScheduleDayCallback(CallbackData, prefix="ScheduleDay"):
    day: int = None
    is_back: bool = False


class ClassRoomScheduleForWeekAdminCallback(CallbackData, prefix="ClassRoomScheduleForWeekAdmin"):
    class_number: int
    class_letter: str
    day: int = 0
    is_back: bool = False


class EditScheduleCallback(CallbackData, prefix="EditSchedule"):
    class_number: int
    class_letter: str
    day: int = 0
    is_back:bool = False


builder = ReplyKeyboardBuilder()

builder.row(
    KeyboardButton(text="Назад"),
)

back_keyboard = builder.as_markup(resize_keyboard=True)


builder = ReplyKeyboardBuilder()

builder.row(
    KeyboardButton(text="Класс 📖"),
    KeyboardButton(text="Расписание 📝")
)

teacher_keyboard = builder.as_markup(resize_keyboard=True)


builder = ReplyKeyboardBuilder()

builder.row(
    KeyboardButton(text="Моё расписание 📝")
)

pupil_keyboard = builder.as_markup(resize_keyboard=True)


builder = InlineKeyboardBuilder()

builder.row(
    InlineKeyboardButton(text="Просмотр классов", callback_data=ClassRoomsActionsCallback(action="view_all").pack()),
).row(
    InlineKeyboardButton(text="Создать новый класс", callback_data=ClassRoomsActionsCallback(action="create").pack())
)

classrooms_actions_keyboard = builder.as_markup(resize_keyboard=True)

builder = InlineKeyboardBuilder()

for day, day_name in enumerate(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"], start=1):
    builder.row(
        InlineKeyboardButton(text=day_name, callback_data=ScheduleDayCallback(day=day).pack())
    )

schedule_days_keyboard = builder.as_markup(resize_keyboard=True)


builder = InlineKeyboardBuilder()

builder.row(
    InlineKeyboardButton(text="Назад", callback_data=ScheduleDayCallback(day=0, is_back=True).pack())
)

back_to_schedule_days_keyboard = builder.as_markup(resize_keyboard=True)


# builder = InlineKeyboardBuilder()

# builder.row(
#     InlineKeyboardButton(text="✅ Подтвердить", callback_data=ActionsWithEditedScheduleCallback(action="accept").pack())
# ).row(
#     InlineKeyboardButton(text="✅ Подтвердить + 🔔", callback_data=ActionsWithEditedScheduleCallback(action="accept_and_notify").pack())
# ).row(
#     InlineKeyboardButton(text="❌ Отменить", callback_data=ActionsWithEditedScheduleCallback(action="cancel").pack())
# )
