from django.contrib import admin
from .models import Category, Location, Asset, AssetEvent


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('building', 'floor', 'room')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'category', 'location', 'status', 'tag_code', 'last_seen')
    list_filter = ('status', 'category')
    search_fields = ('name', 'serial_number', 'tag_code')


@admin.register(AssetEvent)
class AssetEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'asset', 'event_type', 'actor', 'from_location', 'to_location', 'from_user', 'to_user')
    list_filter = ('event_type',)
    search_fields = ('asset__name', 'asset__serial_number', 'actor__username', 'note')
    readonly_fields = ('created_at',)
