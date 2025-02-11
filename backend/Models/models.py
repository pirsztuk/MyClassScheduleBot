from django.db import models
from django.utils.crypto import get_random_string
import string


# ---------------------------------------
# 1. Schools
# ---------------------------------------
class School(models.Model):
    """
    Stores base info about a school or a college 
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# ---------------------------------------
# 2. Users
# ---------------------------------------
ROLE_CHOICES = (
    ('teacher', 'Teacher'),
    ('student', 'Student'),
)

class User(models.Model):
    """
    User, that has:
      - role (`student`/`teacher`)
      - relation to an exact school (for teacher)
      - relation to an exact school and an exact class (for student)
      - Telegram-ID
    """
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student') # Can be `student` or `teacher`
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
    )
    school_class = models.ForeignKey(
        'SchoolClass',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='students',
    )
    telegram_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


# ---------------------------------------
# 3. School Class
# ---------------------------------------
class SchoolClass(models.Model):
    """
    School class: 1A, 2Б, ..., 11Г etc.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    grade = models.PositiveSmallIntegerField(help_text='Class grade (1-11)')
    letter = models.CharField(max_length=5, help_text='Class letter (А, Б, В, ...)', default='A')

    def generate_identifier():
        return get_random_string(32, allowed_chars=string.ascii_uppercase)

    identifier = models.CharField(
        max_length=32, default=generate_identifier
    )

    class Meta:
        unique_together = ('school', 'grade', 'letter')
        ordering = ['grade', 'letter']

    def __str__(self):
        return self.get_class_name()

    def get_class_name(self):
        """Returns Class name in such format: `11 "A"`"""
        return f'{self.grade} "{self.letter}"'


# ---------------------------------------
# 4. Schedule (Main Level)
# ---------------------------------------
class ClassSchedule(models.Model):
    """
    «Version» of schedule for the exact class.
    Usually there is one schedule, but if requested
    it's possible to store few of "version" and switch them
    """
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='schedules')
    name = models.CharField(max_length=255, default='Основное расписание')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Расписание [{self.name}] - {self.school_class.get_class_name()}'


# ---------------------------------------
# 5. Days of schedule
# ---------------------------------------
DAY_CHOICES = (
    (0, 'Понедельник'),
    (1, 'Вторник'),
    (2, 'Среда'),
    (3, 'Четверг'),
    (4, 'Пятница'),
    (5, 'Суббота'),
)

class ScheduleDay(models.Model):
    """
    Contains one day of the week as a part of the week schedule.
    """
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name='days')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)

    class Meta:
        ordering = ['day_of_week']
        unique_together = ('schedule', 'day_of_week')

    def __str__(self):
        return f'{self.get_day_of_week_display()} ({self.schedule})'

    def get_day_name(self):
        """Returns the name of the day of the week (e.g., 'Понедельник')"""
        return dict(DAY_CHOICES).get(self.day_of_week, 'Unknown (Error code: ScheduleDay.get_day_name)')


# ---------------------------------------
# 6. Lessons
# ---------------------------------------
class Lesson(models.Model):
    """
    The exact lesson as a part of the exact day
    Contains info: `time`, `subject_name`, `order`
    """
    day = models.ForeignKey(ScheduleDay, on_delete=models.CASCADE, related_name='lessons')
    subject_name = models.CharField(max_length=255)

    start_time = models.TimeField()
    end_time = models.TimeField()

    order = models.PositiveSmallIntegerField(
        default=0,
    )

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f'{self.subject_name} ({self.day.get_day_name()})'

    def get_lesson_period(self):
        """Lesson period in a pretty format"""
        return f'{self.start_time.strftime("%H:%M")} - {self.end_time.strftime("%H:%M")}'