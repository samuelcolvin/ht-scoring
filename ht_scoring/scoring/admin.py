from ht_scoring.scoring.models import Group, Competition, Round, Competitor, Fence
from django.contrib import admin

class RoundInline(admin.TabularInline):
	model = Round
	extra = 1
	exclude = ('place',)
	
class CompetitorAdmin(admin.ModelAdmin):
	inlines = [RoundInline]
	list_per_page = 500
	list_display = ('num_name', 'horse', 'group', 'total_rounds')
	
class CompetitionAdmin(admin.ModelAdmin):
#	inlines = [RoundInline]
	list_display = ('name', 'optimum_time', 'fences', 'entries')
	
class FenceInline(admin.TabularInline):
	model = Fence
	extra = 1
	
class FenceAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'competition', 'faults', 'eliminated', 'round')
	list_per_page = 500

def set_time_start_zero(modeladmin, request, queryset):
	queryset.update(time_start=0)

set_time_start_zero.short_description = "Set the Start time to 0"

class RoundAdmin(admin.ModelAdmin):
	inlines = [FenceInline]
	list_per_page = 500
	list_filter = ['competition']
	actions=[set_time_start_zero]
	list_display = ('competitor_num_name', 'competition_name', 'place', 'faults_string', 'time_start_str', 'time_finish_str',  'time_diff_str')
	
admin.site.register(Group)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Competitor, CompetitorAdmin)
admin.site.register(Fence, FenceAdmin)

#from django_evolution.models import Version, Evolution
#admin.site.unregister(Version)
#admin.site.unregister(Evolution)