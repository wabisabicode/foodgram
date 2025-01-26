from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from common.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH
from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           RecipeShortURL, ShoppingCartItem, Tag)
from users.models import Subscription

from .fields import Base64ImageField

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=NAME_MAX_LENGTH,
        required=True,
        validators=(
            UniqueValidator(
                queryset=User.objects.all(),
                message='This user is already in use.'),
        ),
        error_messages={
            'invalid':
                'Username contains invalid characters. '
                'Only letters, numbers and symbols are allowed '
                '@/./+/-/_.'
        }
    )
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        required=True,
        validators=(
            UniqueValidator(
                queryset=User.objects.all(),
                message='This email is already in use.'
            ),
        )
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')

        user = super().create(validated_data)
        user.set_password(password)
        user.save()

        return user


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, creator=obj).exists()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'avatar', 'is_subscribed')


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        required=True, style={'input_type': 'password'})
    current_password = serializers.CharField(
        required=True, style={'input_type': 'password'})


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=True)
    password = serializers.CharField(
        required=True, style={'input_type': 'password'})


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True, allow_null=True)
    avatar_url = serializers.SerializerMethodField(
        'get_avatar_url',
        read_only=True,
    )

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class TagReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                {'ingredients': 'Amount should be more than 0'})
        return value

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                {'ingredients': f'Ingredient with id {value} does not exist.'})
        return value


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'image', 'name', 'cooking_time')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='This recipe is already in your favorites.'
            )
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=True)
    author = CustomUserSerializer(read_only=True)
    tags = TagReadSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipeingredients')

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return ShoppingCartItem.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True, allow_null=True)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    ingredients = IngredientAmountSerializer(required=True, many=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def validate_tags(self, tags):
        unique_tags = set(tags)

        if len(unique_tags) != len(tags):
            raise serializers.ValidationError(
                {'tags': 'Tag should be provided only once'}
            )

        return list(unique_tags)

    def validate_ingredients(self, ingredients):
        unique_ingredient_ids = set()

        for ingredient in ingredients:
            ingredient_id = ingredient.get('id')

            if ingredient_id in unique_ingredient_ids:
                raise serializers.ValidationError(
                    {'ingredients': 'Ingredient should be provided only once'}
                )
            else:
                unique_ingredient_ids.add(ingredient_id)

        return ingredients

    def validate(self, data):
        tags = data.get('tags')

        if not tags:
            raise serializers.ValidationError(
                {'tags': 'This field is required and cannot be empty.'}
            )

        ingredients = data.get('ingredients')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required and cannot be empty.'}
            )

        return super().validate(data)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        request = self.context.get('request')
        recipe = Recipe.objects.create(
            **validated_data, author=request.user)

        recipe.tags.set(tags)

        create_ingredients(recipe, ingredients_data)

        recipe_short_url = RecipeShortURL.objects.create(recipe=recipe)
        recipe_short_url.generate_hash()

        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        instance = super().update(instance, validated_data)

        if tags_data:
            instance.tags.set(tags_data)

        instance.recipeingredients.all().delete()
        create_ingredients(instance, ingredients_data)

        instance.save()
        return instance

    def to_representation(self, instance):
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        return read_serializer.data


class RecipeShortURLSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    def get_short_link(self, obj):
        request = self.context.get('request')
        base_path = request.build_absolute_uri('/')
        short_url = f'{base_path}s/' + obj.hash
        return short_url

    class Meta:
        model = RecipeShortURL
        fields = ('short_link',)


class CreatorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['subscriber', 'creator'],
                message='You have already subscribed to this creator.'
            )
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, creator=obj).exists()

    def get_recipes_count(self, obj):
        request = self.context.get('request')
        return Recipe.objects.filter(author=request.user).count()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')

        if limit is not None:
            try:
                limit = int(limit)
                if limit > 0:
                    data['recipes'] = data['recipes'][:limit]
            except ValueError:
                raise serializers.ValidationError(
                    'Invalid recipes_limit value')

        return data


def create_ingredients(recipe, ingredients_data):
    recipe_ingredients = []

    for ingredient_data in ingredients_data:
        ingredient = get_object_or_404(
            Ingredient, id=ingredient_data.get('id'))

        recipe_ingredients.append(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount')
            )
        )

    RecipeIngredient.objects.bulk_create(recipe_ingredients)
