# Generated by Django 5.1.4 on 2025-01-02 12:57

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empapp', '0006_alter_attendance_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckInOut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date(2025, 1, 2))),
                ('check_in', models.TimeField(blank=True, null=True)),
                ('check_out', models.TimeField(blank=True, null=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empapp.employee')),
            ],
        ),
    ]
