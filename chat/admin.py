from django.contrib import admin
from django.contrib.admin import TabularInline


from .models import *


class MessageTabularInline(TabularInline):
    model = Message
    extra = 1


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'initiator', 'receiver']
    inlines = [
        MessageTabularInline,
    ]
