# Generated by Django 5.0.1 on 2024-03-06 01:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0010_order_seq_number_alter_order_order_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='time_arrive',
            new_name='time_arrival',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='use_foto',
            new_name='use_photo',
        ),
    ]
