from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Work(models.Model):
    file = models.FileField("Select word file", validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
                            upload_to="media/")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

