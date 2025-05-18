from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
import csv
from django.db.models import Sum
from .models import User, Purchase
from enseignants.models import Formation, Course
from .models import CourseSubmission 
# ✅ Export to CSV
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    response.write('\ufeff')  # To handle accents correctly in Excel
    writer = csv.writer(response)
    writer.writerow([field.name for field in queryset.model._meta.fields])
    for obj in queryset:
        writer.writerow([getattr(obj, field.name) for field in queryset.model._meta.fields])
    return response
export_to_csv.short_description = "Exporter en CSV"

# ✅ User Admin
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'get_full_name', 'is_student', 'is_teacher', 'is_staff', 'date_joined')
    list_filter = ('is_student', 'is_teacher', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = [export_to_csv, 'ban_users']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'cv')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_student', 'is_teacher')}),
        ('Dates importantes', {'fields': ('date_joined',)}),
        ('Groupes et permissions', {'fields': ('groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_student', 'is_teacher', 'is_staff')}
        ),
    )

    def ban_users(self, request, queryset):
        queryset.update(is_active=False)
    ban_users.short_description = "Bannir les utilisateurs sélectionnés"

# ✅ Formation Admin
class FormationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'teacher', 'prix', 'created_at', 'is_approved')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'created_at')
    search_fields = ('titre', 'description')
    actions = ['approve_formations', export_to_csv]

    def approve_formations(self, request, queryset):
        queryset.update(is_approved=True)
    approve_formations.short_description = "Approuver les formations sélectionnées"

# ✅ Submission Admin
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'submitted_at', 'grade')
    list_editable = ('grade',)
    list_filter = ('course', 'submitted_at')
    search_fields = ('student__email', 'course__titre')

# ✅ Purchase Admin
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('student', 'formation', 'purchased_at', 'is_paid')
    list_filter = ('is_paid', 'purchased_at', 'formation')
    search_fields = ('student__email', 'formation__titre')
    actions = [export_to_csv]

# ✅ Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Formation, FormationAdmin)
admin.site.register(Course)
admin.site.register(CourseSubmission, SubmissionAdmin)
admin.site.register(Purchase, PurchaseAdmin)

admin.site.site_header = "Administration de la Plateforme Éducative"
admin.site.site_title = "Plateforme Éducative"
admin.site.index_title = "Tableau de bord"
