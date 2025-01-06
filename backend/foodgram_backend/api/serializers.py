from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'avatar')


# class TokenSerializer(serializer):
#     class Meta:
#         model = User
#         fields = ('email', 'id', 'username',
#                   'first_name', 'last_name', 'avatar')


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254, required=True)
    password = serializers.CharField(
        required=True, style={'input_type': 'password'})

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.user = None

    # def validate(self, attrs):
    #     password = attrs.get('password')
    #     email = attrs.get('email')
        # print(email)

        # self.user = authenticate(email=email, password=password)

        # if not self.user:
        #     raise serializers.ValidationError('Invalid credentials')
        # return attrs
