from django.contrib import admin
from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group')
    list_editable = ('group', )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'description',
        'slug',
    )
    list_editable = ('title', 'slug', )
    search_fields = ('slug', 'title', )
    list_filter = ('slug', )


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'post',
        'text',
        'author',
        'created',
    )
    list_editable = ('text',)
    search_fields = ('author', 'created', 'post', )
    list_filter = ('post', )


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
