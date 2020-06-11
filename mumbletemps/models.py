from django.db import models
from allianceauth.eveonline.models import EveCharacter

# Create your models here.


class TempLink(models.Model):
    expires = models.IntegerField()
    link_ref = models.CharField(max_length=20, unique=True)
    creator = models.ForeignKey(
        EveCharacter, on_delete=models.SET_NULL, null=True, default=None
    )

    class Meta:
        permissions = (("create_new_links", "Can Create Temp Links"),)

    def __str__(self):
        return "Link {} - {}".format(self.link_ref, self.expires)


class TempUser(models.Model):
    username = models.CharField(
        max_length=200,
        unique=True,
        help_text="Mumble username (will be generated using NameFormatter)",
    )
    password = models.CharField(max_length=20, help_text="Temporary token")
    expires = models.IntegerField(help_text="Unix timestamp when token expires")

    def __str__(self):
        return f"Temp User: {self.username}"
