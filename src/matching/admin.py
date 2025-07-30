from django.contrib import admin
from matching.models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'vacancy', 'score', 'match_quality')
    list_filter = ('score',)
