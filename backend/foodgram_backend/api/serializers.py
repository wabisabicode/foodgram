from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer

# from users.models import FGUser
# from recipe.models import *

User = get_user_model()


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name')
