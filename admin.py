from django.contrib import admin
from models import UpFile
import os

class PathFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'id'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'path'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        
        ret = [(b, b) for b in set((os.path.dirname(a) if os.path.dirname(a) != '' else a) for a in qs.values_list('path', flat=True))]
        print(ret)
        return ret

    def queryset(self, request, queryset):
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() is not None:
            print(self.value())
            return queryset.filter(path__startswith=self.value(),)
            
class UpFileAdmin(admin.ModelAdmin):
    list_display = ('path', 'label')
    list_editable = ('label',)
    list_filter = ('user', PathFilter) 
    
admin.site.register(UpFile, UpFileAdmin)
