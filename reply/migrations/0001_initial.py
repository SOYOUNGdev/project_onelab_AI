# Generated by Django 5.0.2 on 2024-03-14 20:31

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('community', '0001_initial'),
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('reply_content', models.TextField()),
                ('reply_post_status', models.BooleanField(default=True)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='community.community')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='member.member')),
            ],
            options={
                'db_table': 'tbl_reply',
                'ordering': ['-id'],
            },
        ),
    ]
