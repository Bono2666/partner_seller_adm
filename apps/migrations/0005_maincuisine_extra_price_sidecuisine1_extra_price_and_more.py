# Generated by Django 5.0.6 on 2024-07-08 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0004_areasales_city_areasales_district_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='maincuisine',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='sidecuisine1',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='sidecuisine2',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='sidecuisine3',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='sidecuisine4',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='sidecuisine5',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='subcuisine',
            name='extra_price',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=12),
        ),
    ]