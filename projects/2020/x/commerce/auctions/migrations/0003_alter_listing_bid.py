# Generated by Django 4.0.2 on 2022-09-13 18:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0002_rename_watch_list_watchlist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='bid',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='auctions.bid'),
        ),
    ]