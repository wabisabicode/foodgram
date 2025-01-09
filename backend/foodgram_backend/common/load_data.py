import csv

from recipe.models import Ingredient


def load_ingredients_from_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
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


load_ingredients_from_csv('ingredients.csv')
