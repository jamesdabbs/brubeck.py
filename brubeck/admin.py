from django.contrib import admin

from brubeck import models


class TextAdmin(admin.ModelAdmin):
    """ Allows the convenient lookup of a snippet of text on each object """
    def text(self, obj):
        """ Gets the text of the (first) snippet for `obj` """
        return obj.snippets.all()[0].current_text()

    def last_revised_by(self, obj):
        return obj.snippets.all()[0].revision.user


# Core objects
class SpaceAdmin(TextAdmin):
    list_display = ('id', 'name', 'text', 'last_revised_by')
admin.site.register(models.Space, SpaceAdmin)


class PropertyAdmin(SpaceAdmin):
    pass
admin.site.register(models.Property, PropertyAdmin)


class TraitAdmin(TextAdmin):
    list_display = ('id', 'space', 'property', 'value', 'text',
                    'last_revised_by')
admin.site.register(models.Trait, TraitAdmin)


class ImplicationAdmin(TextAdmin):
    list_display = ('id', 'name', 'text', 'last_revised_by')
admin.site.register(models.Implication, ImplicationAdmin)


# Wiki documents
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('object', 'current_text', 'last_revised_by')

    def last_revised_by(self, obj):
        return obj.revision.user
admin.site.register(models.Snippet, SnippetAdmin)


# Profiles
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'revisions')

    def revisions(self, profile):
        return profile.user.revision_set.count()
admin.site.register(models.Profile, ProfileAdmin)