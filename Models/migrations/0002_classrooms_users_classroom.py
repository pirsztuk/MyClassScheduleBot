# Generated by Django 4.2.17 on 2025-01-23 13:40

import Models.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Models', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassRooms',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ClassRoomIdentifier', models.CharField(default=Models.models.ClassRooms.generate_identifier, max_length=32)),
                ('Name', models.CharField(max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='users',
            name='ClassRoom',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Pupils', to='Models.classrooms'),
        ),
    ]
