from django.contrib import admin

from theatre.models import (
    Actor,
    Genre,
    Performance,
    Play,
    Reservation,
    TheatreHall,
    Ticket,
)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)
    list_display = ("id", "user", "created_at")
    list_filter = ("created_at",)


@admin.register(Play)
class PlayAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    filter_horizontal = ("genres", "actors")


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("play", "theatre_hall", "show_time")
    list_filter = ("theatre_hall", "show_time")


admin.site.register(TheatreHall)
admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Ticket)
