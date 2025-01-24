import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipe.models import Ingredient

PROJECT_DIR = str(settings.BASE_DIR) + '/'


class Command(BaseCommand):
    help = 'Import prepared csv-file with ingredients'

    def add_arguments(self, parser):
        parser.add_argument('input_file', nargs='*', type=str,
                            help='csv-filename with path')

    def handle(self, *args, **options):
        foodgram_dir = str(settings.BASE_DIR).rsplit('/', 2)[0] + '/'
        input_file = foodgram_dir + options['input_file'][0]

        with open(input_file, mode='r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)

            ingredients = []
            for row in csvreader:
                name = row[0].strip()
                measurement_unit = row[1].strip()

                ingredient = Ingredient(
                    name=name,
                    measurement_unit=measurement_unit
                )
                ingredients.append(ingredient)

            Ingredient.objects.bulk_create(ingredients)
