from django.db import models

class MarriageUser(models.Model):
    firstName = models.CharField(max_length=100)
    middleName = models.CharField(max_length=100, null=True, blank=True)
    lastName = models.CharField(max_length=100)

    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "marriage_users"