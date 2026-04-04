from django.db import models

class MarriageUser(models.Model):
    firstName = models.CharField(max_length=100, default='')
    middleName = models.CharField(max_length=100, null=True, blank=True)
    lastName = models.CharField(max_length=100, default='')
    mobile = models.CharField(max_length=15, default='')

    name = models.CharField(max_length=255)  # optional (combined)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "marriage_users"

    def __str__(self):
        return self.email