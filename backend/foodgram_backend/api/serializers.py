import base64

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common.help_functions import generate_random_filename
from recipe.models import Tag, Ingredient, Recipe, Favorite
from recipe.models import RecipeTag, RecipeIngredient

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

    # TODO: change to the real subscription check
    def get_is_subscribed(self, obj):
        return False

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
        return {'id': instance.id, 'name': instance.name, 'slug': instance.slug}

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
        # TODO: change to real shopping cart test
        return False

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

            if not ingredient_id or not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    {'ingredients': f'Ingredient with id {ingredient_id} does not exist'}
                )

            amount = ingredient_data.get('amount')
            if amount <= 0:
                raise serializers.ValidationError(
                    {'ingredients': 'Ingredient amount should be more than 0'}
                )

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
            ingredient = get_object_or_404(Ingredient, id=ingredient_data.get('id'))
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data.get('amount')
            )

        return recipe

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
