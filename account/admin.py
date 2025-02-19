from django.contrib import admin


class AccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'email', 'is_active', 'created_at')
    search_fields = ['username', 'name', 'email']
    list_filter = ()

    readonly_fields = ('id',)
