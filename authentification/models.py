from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import URLValidator
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class TrackingModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CustomUserManager(BaseUserManager):
    def _create_user(self, username, email, password, avatar, first_name, last_name, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')

        if not email:
            raise ValueError('The given email must be set')

        if not avatar:
            avatar = 'https://isocarp.org/app/uploads/2014/05/noimage.jpg'
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, avatar=avatar, first_name=first_name,
                          last_name=last_name, **extra_fields)

        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password, avatar, first_name, last_name, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, avatar, first_name, last_name, **extra_fields)

    def create_superuser(self, username, email, password, avatar, first_name, last_name, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, avatar, first_name, last_name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TrackingModel):
    """
        An abstract user class implementing a fully featured User model with
        admin-compliant permissions.

        Username, password, email, first_name, last_name are required. Other fields are optional.
        """
    username_validator = UnicodeUsernameValidator()

    url_validator = URLValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    avatar = models.URLField(default='https://isocarp.org/app/uploads/2014/05/noimage.jpg',
                             validators=[url_validator], blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'avatar', 'first_name', 'last_name']

    class Meta:
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return str(self.id)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)