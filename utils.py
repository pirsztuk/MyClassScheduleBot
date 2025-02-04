from typing import Union
from qrcode_styled import QRCodeStyled
from PIL import Image
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, NewsNERTagger, Doc
from aiogram.types import Message, KeyboardButton, InlineKeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, BufferedInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from Models import models
import keyboards

# segmenter = Segmenter()
# morph_vocab = MorphVocab()

# emb = NewsEmbedding()
# morph_tagger = NewsMorphTagger(emb)
# syntax_parser = NewsSyntaxParser(emb)
# ner_tagger = NewsNERTagger(emb)


def extract_bare_fullname_from_text(text:str) -> Union[str, None]:

    # doc = Doc(text)
    # doc.segment(segmenter) 
    # doc.tag_morph(morph_tagger)
    # doc.parse_syntax(syntax_parser)
    # doc.tag_ner(ner_tagger)

    # if len(doc.spans) > 0:
    #     doc.spans[0].normalize(morph_vocab)

    #     if len(doc.spans[0].normal.split()) >= 2:
    #         return doc.spans[0].normal


    words = text.split()
    if len(words) != 2:
        return None
    for word in words:
        if not word.isalpha() or not word[0].isupper() or not word[1:].islower():
            return None
    return text


def generate_classrooms(ClassRooms:models.ClassRooms, purpose:str) -> Union[InlineKeyboardMarkup, None]:

    class_numbers = list(map(int, ClassRooms.values_list('Number', flat=True).distinct()))
    class_numbers.sort(reverse=True)
    
    if len(class_numbers) == 0:
        return None
    
    builder = InlineKeyboardBuilder()

    for class_number in class_numbers:

        builder.row(
            InlineKeyboardButton(text=f"{class_number} Параллель", callback_data=keyboards.ViewClassRoomsCallback(class_number=class_number, purpose=purpose).pack()),
        )

    return builder.as_markup(resize_keyboard=True)


def generate_specific_classrooms(ClassRooms:models.ClassRooms, class_number:int, purpose:str) -> Union[InlineKeyboardMarkup, None]:

    class_letters = list(ClassRooms.values_list('Letter', flat=True).distinct())
    class_letters.sort(reverse=True)
    
    if len(class_letters) == 0:
        return None
    
    builder = InlineKeyboardBuilder()

    for class_letter in sorted(class_letters, key=lambda x: x.lower()):

        builder.row(
            InlineKeyboardButton(text=f'{class_number} "{class_letter}" класс', callback_data=keyboards.ViewClassRoomCallback(class_number=class_number, class_letter=class_letter, purpose=purpose).pack()),
        )

    builder.row(
        InlineKeyboardButton(text=f"Назад", callback_data=keyboards.ViewClassRoomCallback(class_number=0, class_letter="$", purpose=purpose, is_back=True).pack()),
    )

    return builder.as_markup(resize_keyboard=True)


def generate_invite_qr(link):

    qr = QRCodeStyled()
    image_buffer = qr.get_buffer(
        data=link, 
        # image=Image.open("image.png"), # temp
        _format="PNG"
    )
    image_buffer.seek(0)

    return BufferedInputFile(image_buffer.getvalue(), filename="qrcode.png")


def generate_classroom_information(ClassRoom:models.ClassRooms):

    pupils = ClassRoom.Pupils.all()
    
    if len(pupils) == 0:
        pupil_list = "Тут пока пусто..."
    else:
        pupil_list = "\n".join([f"{index + 1}. {pupil.Fullname}" for index, pupil in enumerate(pupils)])
    
    class_info = f'Класс {ClassRoom.Number} "{ClassRoom.Letter}"\n\nУченики:\n{pupil_list}\n\nВы можете сгенерировать QR-код для приглашения учеников по кнопке ниже'
    return class_info


def generate_classroom_keyboard(ClassRoom:models.ClassRooms):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=f"Сгенерировать QR-код", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="generate_qr_code").pack()),
    ).row(
        InlineKeyboardButton(text=f"Редактировать", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="edit").pack()),
    ).row(
        InlineKeyboardButton(text=f"Удалить", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="delete").pack()),
    ).row(
        InlineKeyboardButton(text=f"Назад", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="back").pack()),
    )

    return builder.as_markup(resize_keyboard=True)


def generate_delete_keyboard(ClassRoom:models.ClassRooms):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=f"Подтвердить удаление", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="сonfirm_delete").pack()),
    ).row(
        InlineKeyboardButton(text=f"Отменить", callback_data=keyboards.ClassRoomActionCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, action="cancel_delete").pack()),
    )

    return builder.as_markup(resize_keyboard=True)


def generate_week_schedule_for_admin(ClassRoom:models.ClassRooms):

    builder = InlineKeyboardBuilder()
    
    for day, day_name in enumerate(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"], start=1):
        builder.row(
            InlineKeyboardButton(text=day_name, callback_data=keyboards.ClassRoomScheduleForWeekAdminCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, day=day).pack())
        )
    
    builder.row(
        InlineKeyboardButton(text=f"Назад", callback_data=keyboards.ClassRoomScheduleForWeekAdminCallback(class_number=ClassRoom.Number, class_letter=ClassRoom.Letter, is_back=True).pack()),
    )

    return builder.as_markup(resize_keyboard=True)


def generate_edit_classroom_schedule(class_number:int, class_letter:str, day:int, button_text:str):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=f"{button_text}", callback_data=keyboards.EditScheduleCallback(class_number=class_number, class_letter=class_letter, day=day).pack())
    ).row(
        InlineKeyboardButton(text="Назад", callback_data=keyboards.EditScheduleCallback(day=0, class_number=class_number, class_letter=class_letter, is_back=True).pack())
    )

    return builder.as_markup(resize_keyboard=True)