import random
import string

from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework.response import Response

from social_project.settings import EMAIL_HOST_USER


def send_code(email, key='email_verification'):
    # Send the verification code to the email
    verification_code = ''.join(random.choices(string.digits, k=6))

    title = "Account Verification"
    text = f"Hello," \
           f"Thank you for choosing our platform!" \
           f"To complete the account verification process, " \
           "Once you click the link, you will be prompted to enter the verification code provided below:" \
           f"Verification Code: {verification_code} This code is used to ensure the security of your account." \
           f" If you did not request this verification, please ignore this email." \
           f"Thank you, Mahdi Malvandi Social Media"

    send_mail(title, text, EMAIL_HOST_USER, [email])
    cache_key = f'{key}:{email}'

    cache.set(cache_key, verification_code, 60 * 2)
    return Response({'email': email, 'detail': 'verification code sent successfully'})


def check_verification_code(request, key='email_verification'):
    user_email = request.data.get('email')
    verification_code = request.data.get('code')

    if not user_email:
        return {'result': False, 'error': "Email cannot be empty"}

    if not verification_code:
        return {'result': False, 'error': "Code cannot be empty"}
    cache_key = f'{key}:{user_email}'
    stored_verification_code = cache.get(cache_key)

    if stored_verification_code == verification_code:
        cache.delete(cache_key)
        return {'result': True}
    else:
        return {'result': False, 'error': "The verification code either does not exist or has expired"}
