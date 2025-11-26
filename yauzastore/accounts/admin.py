from django.contrib import admin
from .models import UserProfile, UserAgreement


class UserProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('agree_to_privacy_policy',)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserAgreement)
