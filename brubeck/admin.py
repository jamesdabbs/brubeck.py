from django.contrib import admin

from brubeck import models


class TextAdmin(admin.ModelAdmin):
    """ Allows the convenient lookup of a snippet of text on each object """
    def text(self, obj):
        """ Gets the text of the (first) snippet for `obj` """
        return obj.snippets.all()[0].current_text()


# Core objects
class SpaceAdmin(TextAdmin):
    list_display = ('id', 'name', 'text')
admin.site.register(models.Space, SpaceAdmin)


class PropertyAdmin(SpaceAdmin):
    pass
admin.site.register(models.Property, PropertyAdmin)


class TraitAdmin(TextAdmin):
    list_display = ('id', 'space', 'property', 'value', 'text')
admin.site.register(models.Trait, TraitAdmin)


class ImplicationAdmin(TextAdmin):
    list_display = ('id', 'name', 'text')
admin.site.register(models.Implication, ImplicationAdmin)


# Wiki documents
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('object', 'current_text', 'is_proof')

    def is_proof(self, obj):
        return hasattr(obj, 'proof')
admin.site.register(models.Snippet, SnippetAdmin)
