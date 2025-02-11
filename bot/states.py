from aiogram.fsm.state import State, StatesGroup


class PupilSignUp(StatesGroup):
    ClassRoomIdentifier = State()
    Fullname = State()


class ClassRoomCreation(StatesGroup):
    class_number = State()
    class_letter = State()


class ScheduleEditing(StatesGroup):
    class_number = State()
    class_letter = State()
    day = State()
    schedule = State()
