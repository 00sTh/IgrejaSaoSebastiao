from unfold.admin import ModelAdmin


class NewsAdmin(ModelAdmin):
    list_display = ("titulo", "tipo", "publicado", "data_criacao")
    list_filter = ("tipo", "publicado", "data_criacao")
    search_fields = ("titulo", "subtitulo", "conteudo")
    list_editable = ("publicado",)
    date_hierarchy = "data_criacao"


class MassScheduleAdmin(ModelAdmin):
    list_display = ("dia_semana", "horario", "tipo", "nome", "ativo", "ordem")
    list_filter = ("dia_semana", "tipo", "ativo")
    list_editable = ("ativo", "ordem")


class SiteContentAdmin(ModelAdmin):
    list_display = ("secao", "titulo", "ordem")
    search_fields = ("secao", "titulo", "conteudo")
    list_editable = ("ordem",)
    readonly_fields = ("secao",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SiteConfigurationAdmin(ModelAdmin):
    list_display = ("chave", "valor", "descricao")
    search_fields = ("chave", "valor", "descricao")


class ContactInfoAdmin(ModelAdmin):
    list_display = ("tipo", "valor", "icone", "ordem")
    list_filter = ("tipo",)
    list_editable = ("ordem",)
