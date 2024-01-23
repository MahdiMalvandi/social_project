from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone


def user_profile_upload_path(instance, filename):
    return f"profiles/{instance.user.username}/{filename}"


class User(AbstractBaseUser):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username, password and email are required. Other fields are optional.
    """

    GENDER_CHOICES = (
        ('m', 'Male'),
        ('f', 'Female')
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    phone_number = models.BigIntegerField(unique=True, validators=[
        validators.RegexValidator(f'^989[0-3,9]\d{8}$', 'Enter a valid mobile number')
    ])
    profile = models.ImageField(upload_to=user_profile_upload_path, blank=True, null=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    last_seen = models.DateTimeField('last seen date', null=True)
    gender = models.CharField(max_length=5, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    following = models.ManyToManyField('self', through='Follow', related_name='followers', symmetrical=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone_number']

    class Meta:
        db_table = 'users'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_loggedin_user(self):
        """
        Returns True if user has actually logged in with valid credentials.
        """
        return self.phone_number is not None or self.email is not None

    def follow_user(self, user_target):
        """
        Follow the specified user.

        :param user_target: The user to be followed.
        :type user_target: User
        """
        created = Follow.objects.create(follower=self, following=user_target)
        if created:
            return True

    def unfollow_user(self, user_target):
        """
        UnFollow the specified user.

        :param user_target: The user to be followed.
        :type user_target: User
        """
        try:
            follow = Follow.objects.get(follower=self, following=user_target)
        except Follow.DoesNotExist:
            raise Follow.DoesNotExist("The target user does not exist in the user's followings")
        follow.delete()
        return True



class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
