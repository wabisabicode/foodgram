import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common.help_functions import generate_random_filename
from recipe.models import Tag, Ingredient, Recipe, Favorite

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name=generate_random_filename() + '.' + ext)

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


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=True)
    author = CustomUserSerializer(read_only=True)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return False

    def create(self, validated_data):
        request = self.context.get('request')
        recipe = Recipe.objects.create(
            **validated_data, author=request.user)
        return recipe

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
