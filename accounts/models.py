from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import AccountManager

class Account(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)

    projects = models.ManyToManyField(
        "projects.Project",
        through="projects.ProjectMember",
        related_name="users"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = AccountManager()

    def __str__(self):
        return self.email
    
