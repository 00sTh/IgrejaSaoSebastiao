from django.utils.html import format_html
from unfold.admin import ModelAdmin


class GalleryImageAdmin(ModelAdmin):
    list_display = ("titulo", "categoria", "preview_thumb", "ativo", "data_upload")
    list_filter = ("categoria", "ativo", "data_upload")
    search_fields = ("titulo", "descricao")
    list_editable = ("ativo",)
    readonly_fields = ("imagem_thumb", "imagem_medium", "imagem_large", "preview_large")

    def preview_thumb(self, obj):
        if obj.imagem_thumb:
            return format_html('<img src="{}" height="60" style="border-radius:4px" />', obj.imagem_thumb.url)
        if obj.imagem:
            return format_html('<img src="{}" height="60" style="border-radius:4px" />', obj.imagem.url)
        return "-"

    preview_thumb.short_description = "Preview"

    def preview_large(self, obj):
        if obj.imagem_large:
            return format_html('<img src="{}" style="max-width:400px;border-radius:8px" />', obj.imagem_large.url)
        if obj.imagem:
            return format_html('<img src="{}" style="max-width:400px;border-radius:8px" />', obj.imagem.url)
        return "-"

    preview_large.short_description = "Preview Grande"
