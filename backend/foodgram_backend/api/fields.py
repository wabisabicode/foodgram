import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from common.help_functions import generate_random_filename


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr),
                               name=generate_random_filename() + '.' + ext)

        return super().to_internal_value(data)
