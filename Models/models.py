from django.db import models
from django.utils.crypto import get_random_string
import string


class Users(models.Model):

    TelegramId = models.BigIntegerField()  # User's telegram_id
    Fullname = models.CharField(
        max_length=32, null=True
    )  # User must provide Fullname during sign up
    ClassRoom = models.ForeignKey(
        "ClassRooms",
        on_delete=models.CASCADE,
        related_name="Pupils",
        null=True,
    )  # Exists only when UserType.PUPIL

    class UserTypeChoices(models.TextChoices):
        PUPIL = "pupil", "Ученик"
        TEACHER = "teacher", "Учитель"

    UserType = models.CharField(
        max_length=7, choices=UserTypeChoices.choices, null=True
    )


class ClassRooms(models.Model):

    def generate_identifier():
        return get_random_string(32, allowed_chars=string.ascii_uppercase)

    ClassRoomIdentifier = models.CharField(
        max_length=32, default=generate_identifier
    )  # For invitational purposes

    Number = models.CharField(
        max_length=2, null=True
    )  # Class Number (Ex. 11 if Class Name is 11 "A")
    Letter = models.CharField(
        max_length=1, null=True
    )  # Class Letter (Ex. A if Class Name is 11 "A")


class ScheduleDays(models.Model):

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    DAY_CHOICES = (
        (MONDAY, "Понедельник"),
        (TUESDAY, "Вторник"),
        (WEDNESDAY, "Среда"),
        (THURSDAY, "Четверг"),
        (FRIDAY, "Пятница"),
    )

    Classroom = models.ForeignKey(
        ClassRooms, on_delete=models.CASCADE, related_name="ScheduleDays"
    )
    DayOfWeek = models.PositiveSmallIntegerField(choices=DAY_CHOICES)

    class Meta:
        unique_together = ("Classroom", "DayOfWeek")
        ordering = ["DayOfWeek"]


class Lessons(models.Model):
    ScheduleDay = models.ForeignKey(
        ScheduleDays, on_delete=models.CASCADE, related_name="Lessons"
    )
    Order = models.PositiveSmallIntegerField()
    SubjectName = models.CharField(max_length=50)

    class Meta:
        ordering = ["Order"]
