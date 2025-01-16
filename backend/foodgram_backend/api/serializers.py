import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from common.help_functions import generate_random_filename
from recipe.models import Tag, Ingredient, Recipe, Favorite
from recipe.models import RecipeTag, RecipeIngredient, RecipeShortURL
from shopping_cart.models import ShoppingCartItem
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr),
                               name=generate_random_filename() + '.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=150,
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
        max_length=254,
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
    email = serializers.EmailField(max_length=254, required=True)
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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class TagIDSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'name': instance.name,
            'slug': instance.slug
        }

    def to_internal_value(self, tag_id):
        try:
            return Tag.objects.get(id=tag_id)
        except Tag.DoesNotExist:
            raise serializers.ValidationError(
                {'tags': f'Tag with id {tag_id} does not exist'})


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


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


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=True)
    author = CustomUserSerializer(read_only=True)
    tags = TagIDSerializer(many=True)
    ingredients = serializers.SerializerMethodField()

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

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)

        recipe_ingredients_list = []
        for ri in recipe_ingredients:
            recipe_ingredients_list.append(
                {
                    'id': ri.ingredient.id,
                    'name': ri.ingredient.name,
                    'measurement_unit': ri.ingredient.measurement_unit,
                    'amount': ri.amount,
                }
            )

        return recipe_ingredients_list

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'This field is required and cannot be empty.'}
            )

        tags_id_list = []
        for tag in tags:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    {'tags': f'Tag with id {tag.id} does not exist'}
                )

            if tag.id in tags_id_list:
                raise serializers.ValidationError(
                    {'tags': 'Tag should be provided only once'}
                )
            else:
                tags_id_list.append(tag.id)

        return tags

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')

        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'This field is required and cannot be empty.'}
            )

        ingredient_id_list = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')

            if (
                not ingredient_id
                or not Ingredient.objects.filter(id=ingredient_id).exists()
            ):
                raise serializers.ValidationError(
                    {'ingredients': f'id {ingredient_id} does not exist'}
                )

            amount = ingredient_data.get('amount')
            if amount is None:
                raise serializers.ValidationError(
                    {'ingredients': 'Ingredient amount is required'})
            try:
                amount = int(amount)
                if int(amount) <= 0:
                    raise serializers.ValidationError(
                        {'ingredients': 'Amount should be more than 0'}
                    )
            except ValueError:
                raise serializers.ValidationError(
                    {'ingredients': 'Amount must be a valid integer'})

            if ingredient_id in ingredient_id_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ingredient should be provided only once'}
                )
            else:
                ingredient_id_list.append(ingredient_id)

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = self.initial_data.get('ingredients')

        request = self.context.get('request')
        recipe = Recipe.objects.create(
            **validated_data, author=request.user)

        for tag in tags:
            RecipeTag.objects.create(tag=tag, recipe=recipe)

        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data.get('id'))
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount')
            )

        recipe_short_url = RecipeShortURL.objects.create(recipe=recipe)
        recipe_short_url.generate_hash()

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.author = validated_data.get('author', instance.author)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)

        # Tags is given by TagSerializer
        try:
            tags_data = validated_data.pop('tags')
        except KeyError:
            raise serializers.ValidationError(
                {'tags': 'This field is required and cannot be empty.'})

        tags_list = list(tags_data)
        instance.tags.set(tags_list)

        # Ingredients is a SerializerMethodField
        ingredients_data = self.initial_data.get('ingredients')

        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data.get('id'))
            ingredients_list.append(ingredient)
        instance.ingredients.set(ingredients_list)

        instance.save()
        return instance

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


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
