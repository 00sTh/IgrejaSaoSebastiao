from unfold.admin import ModelAdmin


class ContactMessageAdmin(ModelAdmin):
    list_display = ("nome", "email", "lida", "data_criacao")
    list_filter = ("lida", "data_criacao")
    search_fields = ("nome", "email", "mensagem")
    list_editable = ("lida",)
    readonly_fields = ("nome", "email", "mensagem", "data_criacao")
    date_hierarchy = "data_criacao"

    def has_add_permission(self, request):
        return False
