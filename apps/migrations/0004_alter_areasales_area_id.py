# Generated by Django 4.2.4 on 2023-10-09 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0003_alter_distributor_distributor_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='areasales',
            name='area_id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False),
        ),
    ]
