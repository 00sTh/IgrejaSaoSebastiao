"""
Seeds default site content, mass schedules, contacts, and configurations.
Run: python manage.py seed_content
"""

from django.core.management.base import BaseCommand

from apps.parish.models import ContactInfo, MassSchedule, SiteConfiguration, SiteContent


class Command(BaseCommand):
    help = "Seeds default content for the parish website"

    def handle(self, *args, **options):
        self._seed_site_content()
        self._seed_mass_schedules()
        self._seed_contacts()
        self._seed_configurations()
        self.stdout.write(self.style.SUCCESS("Conteúdo padrão criado com sucesso!"))

    def _seed_site_content(self):
        sections = [
            ("hero_titulo", "Igreja São Sebastião", "Título principal do banner"),
            ("hero_subtitulo", "Onde a Fé Encontra a Comunidade em Ponte Nova", "Subtítulo do banner"),
            ("hero_botao", "Ver Horários das Missas", "Texto do botão do banner"),
            ("sobre_titulo", "Seja Bem-Vindo à Nossa Comunidade!", "Título da seção Sobre"),
            (
                "sobre_texto",
                "A Igreja São Sebastião tem sido um farol de fé e esperança para a comunidade de Ponte Nova "
                "por décadas. Convidamos você a fazer parte de nossa família, a encontrar consolo na palavra "
                "e a fortalecer sua espiritualidade.",
                "Texto da seção Sobre",
            ),
            ("horarios_titulo", "Horários Importantes", "Título da seção de horários"),
            ("missas_titulo", "Missas", "Título do card de missas"),
            ("confissoes_titulo", "Confissões", "Título do card de confissões"),
            (
                "confissoes_horarios",
                "Terça a Sexta: 14h às 17h|Sábado: 9h às 12h",
                "Horários de confissão (separados por |)",
            ),
            ("secretaria_titulo", "Secretaria", "Título do card da secretaria"),
            ("secretaria_horarios", "Segunda a Sexta: 13h às 18h", "Horário da secretaria"),
            ("secretaria_telefone", "(31) 3295-1379", "Telefone da secretaria"),
            ("secretaria_email", "contato@igrejasst.org", "Email da secretaria"),
            ("galeria_titulo", "Nossa Igreja em Imagens", "Título da seção galeria"),
            ("historia_titulo", "Nossa História e Legado", "Título da seção história"),
            (
                "historia_texto",
                "<p>Fundada em [Ano de Fundação], a Igreja São Sebastião tem uma rica história de serviço e "
                "evangelização. Desde sua construção, este santuário tem sido um ponto de encontro para "
                "gerações de fiéis, testemunhando momentos de alegria, consolo e renovação da fé.</p>"
                "<p>Nossa paróquia cresceu junto com a cidade de Ponte Nova, adaptando-se aos desafios e "
                "celebrando as vitórias. Pessoas dedicadas, desde os primeiros padres até os voluntários "
                "de hoje, construíram um legado de amor e acolhimento que continua a inspirar.</p>",
                "Texto da história",
            ),
            ("historia_marcos_titulo", "Principais Marcos", "Título dos marcos históricos"),
            (
                "historia_marcos",
                "[Ano]: Fundação da paróquia|[Ano]: Início da construção da atual igreja|"
                "[Ano]: Inauguração e primeira missa solene|[Ano]: Lançamento de importantes projetos sociais",
                "Marcos históricos (separados por |)",
            ),
            ("localizacao_titulo", "Onde Nos Encontrar", "Título da seção localização"),
            (
                "localizacao_endereco",
                "Praça Getúlio Vargas, 92 - Centro Histórico, Pte. Nova - MG, 35430-003",
                "Endereço completo",
            ),
            ("localizacao_telefones", "(31) 98888-6796 / (31) 3881-1401", "Telefones"),
            ("localizacao_email", "contato@igrejasst.org", "Email"),
            (
                "localizacao_mapa",
                "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3739.1906006479735!2d-42.911577723851245"
                "!3d-20.41623625363568!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xa497026b4d46e1"
                "%3A0x5d64af00395326ce!2sIgreja%20Matriz%20de%20S%C3%A3o%20Sebasti%C3%A3o%20-%20Ponte%20Nova"
                "!5e0!3m2!1spt-BR!2sbr!4v1757269101938!5m2!1spt-BR!2sbr",
                "URL do mapa embed",
            ),
            ("contato_titulo", "Entre em Contato", "Título da seção contato"),
            ("contato_subtitulo", "Estamos Prontos para Ajudar", "Subtítulo da seção contato"),
            (
                "contato_texto",
                "Tem dúvidas, sugestões ou precisa de mais informações? Fale conosco!",
                "Texto da seção contato",
            ),
            ("rodape_texto", "Igreja São Sebastião. Todos os direitos reservados.", "Texto do rodapé"),
            ("redes_facebook", "#", "Link do Facebook"),
            ("redes_instagram", "#", "Link do Instagram"),
            ("redes_whatsapp", "#", "Link do WhatsApp"),
        ]

        created = 0
        for i, (secao, titulo, conteudo) in enumerate(sections):
            _, was_created = SiteContent.objects.get_or_create(
                secao=secao,
                defaults={"titulo": titulo, "conteudo": conteudo, "ordem": i},
            )
            if was_created:
                created += 1

        self.stdout.write(f"  SiteContent: {created} seções criadas")

    def _seed_mass_schedules(self):
        schedules = [
            ("segunda", "07:00", "missa", "", 1),
            ("terca", "07:00", "missa", "", 2),
            ("quarta", "07:00", "missa", "", 3),
            ("quinta", "07:00", "missa", "", 4),
            ("sexta", "07:00", "missa", "", 5),
            ("sabado", "19:00", "missa", "", 6),
            ("domingo", "08:00", "missa", "", 7),
            ("domingo", "19:00", "missa", "Missa Solene", 8),
        ]

        if MassSchedule.objects.exists():
            self.stdout.write("  MassSchedule: já existem horários, pulando")
            return

        for dia, hora, tipo, nome, ordem in schedules:
            MassSchedule.objects.create(dia_semana=dia, horario=hora, tipo=tipo, nome=nome, ordem=ordem)
        self.stdout.write(f"  MassSchedule: {len(schedules)} horários criados")

    def _seed_contacts(self):
        contacts = [
            ("telefone", "(31) 0000-0000", "fas fa-phone", 1),
            ("email", "contato@igrejasaosebastiao.com.br", "fas fa-envelope", 2),
            ("endereco", "Rua São Sebastião, 123 - Ponte Nova/MG", "fas fa-map-marker-alt", 3),
        ]

        if ContactInfo.objects.exists():
            self.stdout.write("  ContactInfo: já existem contatos, pulando")
            return

        for tipo, valor, icone, ordem in contacts:
            ContactInfo.objects.create(tipo=tipo, valor=valor, icone=icone, ordem=ordem)
        self.stdout.write(f"  ContactInfo: {len(contacts)} contatos criados")

    def _seed_configurations(self):
        configs = [
            ("site_nome", "Igreja São Sebastião", "Nome do site"),
            ("site_descricao", "Onde a Fé Encontra a Comunidade", "Descrição do site"),
            ("endereco_completo", "Rua São Sebastião, 123 - Centro, Ponte Nova/MG", "Endereço completo"),
            ("mapa_latitude", "-20.4169", "Latitude para o mapa"),
            ("mapa_longitude", "-42.9089", "Longitude para o mapa"),
        ]

        created = 0
        for chave, valor, descricao in configs:
            _, was_created = SiteConfiguration.objects.get_or_create(
                chave=chave,
                defaults={"valor": valor, "descricao": descricao},
            )
            if was_created:
                created += 1

        self.stdout.write(f"  SiteConfiguration: {created} configurações criadas")
