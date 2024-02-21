from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

# ایجاد یک سیگنال برای ورود کاربر
@receiver(user_logged_in)
def user_login(sender, request, user, **kwargs):
    user.is_online = True
    print(f'user {user} logged in and his is_online is {user.is_online}')

# ایجاد یک سیگنال برای خروج کاربر
@receiver(user_logged_out)
def user_logout(sender, request, user, **kwargs):
    user.is_online = False
    print(f'user {user} logged out and his is_online is {user.is_online}')