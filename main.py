import os
import sys
import time
import logging
from datetime import datetime, timedelta
import django
import asyncio
from io import BytesIO

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions
from aiogram.utils.markdown import hbold
from aiogram.utils.deep_linking import create_start_link
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.state import State, StatesGroup

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "MyClassScheduleWebsite.settings"
)
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# Load environment variables
load_dotenv()

# Import Django ORM models
from Models.models import Users, ClassRooms, ScheduleDays, Lessons
import utils
import states
import keyboards

# Extract bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set in the environment variables")

# Excract root admin id from environment variables
try:
    ROOT_ADMIN = int(os.environ["ROOT_ADMIN"])
except KeyError:
    raise ValueError(
        "ROOT_ADMIN is not set in the environment variables. It may cause security threats"
    )
except ValueError:
    raise ValueError("ROOT_ADMIN must be a valid integer")


# Initialize Dispatcher and Router
logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
router = Router()


@router.message(CommandStart())
async def command_start_handler(
    message: types.Message, command: CommandObject, state: FSMContext
) -> None:
    args = command.args

    answer = """Привет! 👋
Я твой помощник с расписанием. Буду держать тебя в курсе, что, где и когда! Заглядывай сюда, чтобы всё знать первым. 🚀"""
    keyboard = None

    if Users.objects.filter(TelegramId=message.from_user.id).exists():

        User = Users.objects.get(TelegramId=message.from_user.id)

        if User.UserType == Users.UserTypeChoices.PUPIL:

            answer = "Привет! 👋 Смотри свое расписание"
            keyboard = keyboards.pupil_keyboard

        elif User.UserType == Users.UserTypeChoices.TEACHER:

            keyboard = keyboards.teacher_keyboard

    elif (
        args
        and len(args) == 32
        and ClassRooms.objects.filter(ClassRoomIdentifier=args).exists()
    ):

        answer = "Привет! 👋\nЯ твой помощник с расписанием. Буду держать тебя в курсе, что, где и когда!\n\nПожалуйста, введите вашу Фамилию и Имя."

        await state.set_state(states.PupilSignUp.Fullname)
        await state.update_data(ClassRoomIdentifier=args)

    await message.answer(answer, reply_markup=keyboard)

    await message.delete()


@router.message(states.PupilSignUp.Fullname)
async def sign_up_pupil_handler(
    message: types.Message, state: FSMContext
) -> None:

    if fullname := utils.extract_bare_fullname_from_text(message.text):

        await state.update_data(Fullname=fullname)

        data = await state.get_data()

        ClassRoom = ClassRooms.objects.filter(
            ClassRoomIdentifier=data["ClassRoomIdentifier"]
        )

        if not ClassRoom.exists():
            return

        ClassRoom = ClassRoom.first()

        Users.objects.create(
            TelegramId=message.from_user.id,
            Fullname=data["Fullname"],
            ClassRoom=ClassRoom,
            UserType=Users.UserTypeChoices.PUPIL,
        )

        await state.clear()

        await message.answer(
            "Поздравляю, регистрация прошла успешно!\n\n"
            "Теперь вы можете взглянуть на свое расписание по кнопке внизу",
            reply_markup=keyboards.pupil_keyboard,
        )

    else:

        await message.answer(
            "Пожалуйста, введите вашу Фамилию и Имя.  \n\nПример: Иванов Иван"
        )


@router.message(Command("add_admin"), F.from_user.id == ROOT_ADMIN)
async def command_add_admin_handler(message: types.Message) -> None:
    """
    Command for adding new admins by telegram_id.
    Available only for ROOT ADMIN
    """

    await message.delete()

    args = message.text.split()[1:]
    if len(args) == 3 and args[0].isdigit():

        User = Users.objects.create(
            TelegramId=int(args[0]),
            Fullname=f"{args[1]} {args[2]}",
            UserType=Users.UserTypeChoices.TEACHER,
        )

        await message.answer(
            f"Создан учитель (id {User.pk}) {args[1]} {args[2]} с TelegramId {args[0]}"
        )
    else:
        await message.answer(
            "Необходимо написать коману в формате `/add_admin 1230154081 Пирштук Роман`"
        )


@router.message(F.text == "Моё расписание 📝")
async def handle_classrooms(message: Message):

    await message.delete()

    if not (
        User := Users.objects.filter(
            TelegramId=message.from_user.id,
            UserType=Users.UserTypeChoices.PUPIL,
        )
    ).exists():
        return

    days = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]
    current_day_index = datetime.now().weekday()
    current_day = days[current_day_index]

    text = f"🗓 Выберите день для расписания.\n\nСегодня: *{current_day}*"

    await message.answer(
        text,
        reply_markup=keyboards.schedule_days_keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(keyboards.ScheduleDayCallback.filter())
async def handle_schedule_days(
    query: CallbackQuery,
    callback_data: keyboards.ScheduleDayCallback,
    state: FSMContext,
):

    if not (
        User := Users.objects.filter(
            TelegramId=query.from_user.id, UserType=Users.UserTypeChoices.PUPIL
        )
    ).exists():
        return

    days = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
    ]

    if callback_data.is_back:

        current_day_index = datetime.now().weekday()
        current_day = days[current_day_index]

        text = f"🗓 Выберите день для расписания.\n\nСегодня: *{current_day}*"

        await query.message.delete()

        await query.message.answer(
            text,
            reply_markup=keyboards.schedule_days_keyboard,
            parse_mode="Markdown",
        )
        return

    ClassRoom = User.first().ClassRoom

    if not (
        ScheduleDay := ClassRoom.ScheduleDays.filter(
            DayOfWeek=callback_data.day
        )
    ).exists():
        await query.message.answer(
            "Твой учитель еще не добавил расписания на этот день😓"
        )
        return

    ScheduleDay = ScheduleDay.first()

    text_lines = []
    for lesson in ScheduleDay.Lessons.all():
        text_lines.append(f"{lesson.Order}. {lesson.SubjectName}")

    lessons_answer = "\n".join(text_lines)

    await query.message.delete()

    await query.message.answer(
        f"Вот твое расписание на *{days[callback_data.day-1]}*:\n\n{lessons_answer}",
        reply_markup=keyboards.back_to_schedule_days_keyboard,
        parse_mode="Markdown",
    )


@router.message(F.text == "Класс 📖")
async def handle_classrooms(message: Message):

    await message.delete()

    if not Users.objects.filter(
        TelegramId=message.from_user.id, UserType=Users.UserTypeChoices.TEACHER
    ).exists():
        return

    await message.answer(
        "Действия с Классами 📖",
        reply_markup=keyboards.classrooms_actions_keyboard,
    )


@router.message(F.text == "Расписание 📝")
async def handle_schedule(message: Message):

    await message.delete()

    if not Users.objects.filter(
        TelegramId=message.from_user.id, UserType=Users.UserTypeChoices.TEACHER
    ).exists():
        return

    answer = "Действия с Расписанием 📝"
    keyboard = utils.generate_classrooms(
        ClassRooms.objects.all(), purpose="view_schedule"
    )

    if not keyboard:
        answer = "Для начала необходимо создать класс"

    await message.answer(answer, reply_markup=keyboard)


@router.callback_query(keyboards.ClassRoomsActionsCallback.filter())
async def handle_classrooms_action(
    query: CallbackQuery,
    callback_data: keyboards.ClassRoomsActionsCallback,
    state: FSMContext,
):

    await query.message.delete()

    match callback_data.action:
        case "view_all":
            answer = "Выберите параллель:"
            keyboard = utils.generate_classrooms(
                ClassRooms.objects.all(), purpose="view_classrooms"
            )
            if not keyboard:
                answer = "Для начала необходимо создать класс"

            await query.message.answer(answer, reply_markup=keyboard)

        case "create":
            await query.message.answer(
                "Введите цифру класса:", reply_markup=keyboards.back_keyboard
            )
            await state.set_state(states.ClassRoomCreation.class_number)


@router.message(states.ClassRoomCreation.class_number)
async def handle_classroom_number(message: Message, state: FSMContext):

    if message.text == "Назад":
        await message.delete()
        await state.clear()
        answer = """Привет! 👋\nЯ твой помощник с расписанием. Буду держать тебя в курсе, что, где и когда! Заглядывай сюда, чтобы всё знать первым. 🚀"""
        keyboard = keyboards.teacher_keyboard
        await message.answer(answer, reply_markup=keyboard)
        return

    if not message.text in map(str, range(1, 12)):
        await message.delete()
        await message.answer("Напишите только цифру класса!")
        return

    await state.update_data(class_number=message.text)
    await message.answer(
        "Введите букву класса:", reply_markup=keyboards.back_keyboard
    )
    await state.set_state(states.ClassRoomCreation.class_letter)


@router.message(states.ClassRoomCreation.class_letter)
async def handle_classroom_letter(message: Message, state: FSMContext):

    await message.delete()

    if message.text == "Назад":
        await state.clear()
        answer = """Привет! 👋\nЯ твой помощник с расписанием. Буду держать тебя в курсе, что, где и когда! Заглядывай сюда, чтобы всё знать первым. 🚀"""
        keyboard = keyboards.teacher_keyboard
        await message.answer(answer, reply_markup=keyboard)
        return

    if len(message.text.upper()) != 1:
        await message.answer("Напишите только букву класса!")
        return

    await state.update_data(class_letter=message.text)

    data = await state.get_data()

    ClassRoom = ClassRooms.objects.create(
        Number=data["class_number"], Letter=data["class_letter"]
    )

    link = await create_start_link(bot, f"{ClassRoom.ClassRoomIdentifier}")
    photo = utils.generate_invite_qr(link)

    await message.answer(
        f'Класс {data["class_number"]} "{data["class_letter"]}" создан!\n\nВы можете пригласить учеников по QR-коду ниже',
        reply_markup=keyboards.teacher_keyboard,
    )
    await state.clear()

    await bot.send_photo(
        chat_id=message.from_user.id,
        photo=photo,
        caption="Подключайся к Моему Расписанию!",
    )


@router.callback_query(keyboards.ViewClassRoomsCallback.filter())
async def handle_view_classrooms(
    query: CallbackQuery, callback_data: keyboards.ViewClassRoomsCallback
):

    await query.message.delete()
    keyboard = utils.generate_specific_classrooms(
        ClassRooms.objects.filter(Number=callback_data.class_number),
        class_number=callback_data.class_number,
        purpose=callback_data.purpose,
    )

    await query.message.answer("Выберите класс:", reply_markup=keyboard)


@router.callback_query(keyboards.ViewClassRoomCallback.filter())
async def handle_view_classroom(
    query: CallbackQuery, callback_data: keyboards.ViewClassRoomCallback
):

    await query.message.delete()

    if callback_data.is_back:
        keyboard = utils.generate_classrooms(
            ClassRooms.objects.all(), purpose=callback_data.purpose
        )
        await query.message.answer(
            "Выберите параллель:", reply_markup=keyboard
        )
        return

    if not ClassRooms.objects.filter(
        Number=callback_data.class_number, Letter=callback_data.class_letter
    ).exists():
        return

    answer = None
    keyboard = None

    ClassRoom = ClassRooms.objects.filter(
        Number=callback_data.class_number, Letter=callback_data.class_letter
    ).first()

    match callback_data.purpose:

        case "view_classrooms":

            answer = utils.generate_classroom_information(ClassRoom)
            keyboard = utils.generate_classroom_keyboard(ClassRoom)

        case "view_schedule":

            answer = f'🗓 Выберите день для редактирования расписания {callback_data.class_number} "{callback_data.class_letter}"'
            keyboard = utils.generate_week_schedule_for_admin(ClassRoom)

    await query.message.answer(
        answer, reply_markup=keyboard, parse_mode="Markdown"
    )


@router.callback_query(
    keyboards.ClassRoomScheduleForWeekAdminCallback.filter()
)
async def handle_view_schedule_by_teacher(
    query: CallbackQuery,
    callback_data: keyboards.ClassRoomScheduleForWeekAdminCallback,
):

    await query.message.delete()

    if callback_data.is_back:
        keyboard = utils.generate_specific_classrooms(
            ClassRooms.objects.filter(Number=callback_data.class_number),
            class_number=callback_data.class_number,
            purpose="view_schedule",
        )
        await query.message.answer("Выберите класс:", reply_markup=keyboard)
        return

    if not (
        ClassRoom := ClassRooms.objects.filter(
            Number=callback_data.class_number,
            Letter=callback_data.class_letter,
        )
    ).exists():
        return

    ClassRoom = ClassRoom.first()

    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    day_name = days_of_week[callback_data.day - 1]
    keyboard = None

    if (
        not (
            ScheduleDay := ClassRoom.ScheduleDays.filter(
                DayOfWeek=callback_data.day
            )
        ).exists()
        or ScheduleDay.first().Lessons.count() == 0
    ):
        answer = f'На {day_name} у {callback_data.class_number} "{callback_data.class_letter}" нет расписания'
        keyboard = utils.generate_edit_classroom_schedule(
            callback_data.class_number,
            callback_data.class_letter,
            callback_data.day,
            "Создать",
        )

    else:
        ScheduleDay = ScheduleDay.first()

        text_lines = []
        for lesson in ScheduleDay.Lessons.all():
            text_lines.append(f"{lesson.Order}. {lesson.SubjectName}")

        lessons_answer = "\n".join(text_lines)

        answer = f'Расписание на *{day_name}* у {callback_data.class_number} "{callback_data.class_letter}":\n\n{lessons_answer}'
        keyboard = utils.generate_edit_classroom_schedule(
            callback_data.class_number,
            callback_data.class_letter,
            callback_data.day,
            "Редактировать",
        )

    await query.message.answer(
        answer, reply_markup=keyboard, parse_mode="Markdown"
    )


@router.callback_query(keyboards.EditScheduleCallback.filter())
async def handle_edit_schedule(
    query: CallbackQuery,
    callback_data: keyboards.EditScheduleCallback,
    state: FSMContext,
):

    await query.message.delete()

    if not (
        ClassRoom := ClassRooms.objects.filter(
            Number=callback_data.class_number,
            Letter=callback_data.class_letter,
        )
    ).exists():
        return

    ClassRoom = ClassRoom.first()

    if callback_data.is_back:
        answer = f'🗓 Выберите день для редактирования расписания {callback_data.class_number} "{callback_data.class_letter}"'
        keyboard = utils.generate_week_schedule_for_admin(ClassRoom)
        await query.message.answer(
            answer, reply_markup=keyboard, parse_mode="Markdown"
        )
        return

    if not (
        ScheduleDay := ClassRoom.ScheduleDays.filter(
            DayOfWeek=callback_data.day
        )
    ).exists():
        ScheduleDay = ScheduleDays.objects.create(
            Classroom=ClassRoom, DayOfWeek=callback_data.day
        )
    else:
        ScheduleDay = ScheduleDay.first()

    text_lines = [
        f"{lesson.SubjectName}" for lesson in ScheduleDay.Lessons.all()
    ]

    if len(text_lines) > 0:
        lessons_answer = "\n".join(text_lines)
    else:
        lessons_answer = "Первый урок\nВторой урок\nТретий урок"

    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    day_name = days_of_week[callback_data.day - 1]

    await state.set_state(states.ScheduleEditing.schedule)

    await state.update_data(class_number=callback_data.class_number)
    await state.update_data(class_letter=callback_data.class_letter)
    await state.update_data(day=callback_data.day)

    await query.message.answer(
        f"Расписание на *{day_name}*:```\n\n{lessons_answer}```\n\n*Нажмите на текст, чтобы его скопировать. Вводить уроки необходимо в таком же формате (без цифр)*",
        parse_mode="Markdown",
    )


@router.message(states.ScheduleEditing.schedule)
async def handle_schedule_editing(message: Message, state: FSMContext):

    await message.delete()

    state_data = await state.get_data()

    if not (
        ClassRoom := ClassRooms.objects.filter(
            Number=state_data["class_number"],
            Letter=state_data["class_letter"],
        )
    ).exists():
        return

    ClassRoom = ClassRoom.first()

    if not (
        ScheduleDay := ClassRoom.ScheduleDays.filter(
            DayOfWeek=state_data["day"]
        )
    ).exists():
        ScheduleDay = ScheduleDays.objects.create(
            Classroom=ClassRoom, DayOfWeek=state_data["day"]
        )
    else:
        ScheduleDay = ScheduleDay.first()

    ScheduleDay.Lessons.all().delete()

    for index, lesson_name in enumerate(message.text.split("\n")):

        Lessons.objects.create(
            ScheduleDay=ScheduleDay, Order=index + 1, SubjectName=lesson_name
        )

    text_lines = []
    for lesson in ScheduleDay.Lessons.all():
        text_lines.append(f"{lesson.Order}. {lesson.SubjectName}")

    lessons_answer = "\n".join(text_lines)

    days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    day_name = days_of_week[state_data["day"] - 1]

    answer = f'Расписание на *{day_name}* у {state_data["class_number"]} "{state_data["class_letter"]}":\n\n{lessons_answer}'
    keyboard = utils.generate_edit_classroom_schedule(
        state_data["class_number"],
        state_data["class_letter"],
        state_data["day"],
        "Редактировать",
    )

    await message.answer(answer, reply_markup=keyboard, parse_mode="Markdown")

    text = f"🚨 У тебя обновилось расписание 📢\nТвое новое расписание на *{day_name}*:\n\n{lessons_answer}"

    for Pupil in ClassRoom.Pupils.all():

        try:

            await bot.send_message(
                chat_id=Pupil.TelegramId, text=text, parse_mode="Markdown"
            )

        except Exception:
            ...


@router.callback_query(keyboards.ClassRoomActionCallback.filter())
async def handle_view_classroom(
    query: CallbackQuery, callback_data: keyboards.ClassRoomActionCallback
):

    match callback_data.action:
        case "generate_qr_code":
            ClassRoom = ClassRooms.objects.filter(
                Number=callback_data.class_number,
                Letter=callback_data.class_letter,
            )

            if not ClassRoom.exists():
                return

            ClassRoom = ClassRoom.first()

            link = await create_start_link(
                bot, f"{ClassRoom.ClassRoomIdentifier}"
            )
            photo = utils.generate_invite_qr(link)

            await bot.send_photo(
                chat_id=query.from_user.id,
                photo=photo,
                caption="Подключайся к Моему Расписанию!",
            )

        case "edit":
            # await query.message.delete()

            await query.answer("Пока класс редактировать нельзя")

        case "delete":
            # await query.message.delete()

            await query.answer("Пока класс удалить нельзя")

        case "back":
            await query.message.delete()

            keyboard = utils.generate_specific_classrooms(
                ClassRooms.objects.filter(Number=callback_data.class_number),
                class_number=callback_data.class_number,
                purpose="view_classrooms",
            )

            await query.message.answer(
                "Выберите класс:", reply_markup=keyboard
            )


async def start_bot() -> None:

    global bot

    bot = Bot(
        token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(router)
    asyncio.run(start_bot())
