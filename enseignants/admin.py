from django.contrib import admin
from .models import EnseignantProfile

@admin.register(EnseignantProfile)
class EnseignantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'cv')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('user__is_active',)
    raw_id_fields = ('user',)  # For better performance with many users
