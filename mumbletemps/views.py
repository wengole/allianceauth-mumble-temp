import datetime

from allianceauth.authentication.models import get_guest_state, State
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import NameFormatter
from allianceauth.services.modules.mumble.auth_hooks import MumbleService
from dataclasses import dataclass, field, InitVar
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import generic
from esi.decorators import _check_callback
from esi.views import sso_redirect

from . import app_settings
from .forms import TempLinkCreateForm, TempLinkLoginForm
from .models import TempLink, TempUser


@dataclass
class PseudoProfile:
    main_character: EveCharacter
    state: State = get_guest_state()


@dataclass
class PseudoUser:
    username: str
    profile: PseudoProfile = field(init=False)
    main_character: InitVar[EveCharacter] = None

    def __post_init__(self, main_character: EveCharacter):
        self.profile = PseudoProfile(main_character)


@method_decorator(permission_required("mumbletemps.create_new_links"), name="dispatch")
class Index(LoginRequiredMixin, generic.FormView):
    template_name = "mumbletemps/index.html"
    form_class = TempLinkCreateForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tl_list"] = TempLink.objects.filter(
            expires__gte=datetime.datetime.utcnow()
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        return ctx

    def form_valid(self, form):
        expiry = datetime.datetime.utcnow().replace(
            tzinfo=timezone.utc
        ) + datetime.timedelta(hours=int(form.cleaned_data["duration"]))
        tl = TempLink.objects.create(
            creator=self.request.user.profile.main_character,
            link_ref=get_random_string(15),
            expires=expiry.timestamp(),
        )
        tl.save()
        ctx = self.get_context_data(tl=tl)
        return self.render_to_response(ctx)


class TempLinkLogin(generic.FormView):
    form_class = TempLinkLoginForm
    template_name = "mumbletemps/login.html"

    def get(self, request, *args, **kwargs):
        link_ref = kwargs.get("link_ref", "")
        link = get_object_or_404(TempLink, link_ref=link_ref)
        token = _check_callback(request)
        sso = request.GET.get("sso", "False") == "True"
        if token:
            return self.link_sso(token, link)
        if app_settings.MUMBLE_TEMPS_FORCE_SSO or sso:
            return sso_redirect(request, scopes=["publicData"])
        ctx = self.get_context_data(link=link)
        return self.render_to_response(ctx)

    def form_valid(self, form):
        name = form.cleaned_data["name"]
        association = form.cleaned_data["association"]
        display_name = (
            f"{app_settings.MUMBLE_TEMPS_LOGIN_PREFIX}[{association.upper()}] {name}"
        )
        return self.create_temp_user(display_name)

    def create_temp_user(self, display_name: str):
        link_ref = self.kwargs.get("link_ref", "")
        link = get_object_or_404(TempLink, link_ref=link_ref)
        password = get_random_string(15)
        temp_user, created = TempUser.objects.get_or_create(
            username=display_name,
            defaults=dict(password=password, expires=link.expires, temp_link=link),
        )
        if not created:
            temp_user.password = password
            temp_user.expires = link.expires
            temp_user.temp_link = link
            temp_user.save()

        connect_url = f"{display_name}:{password}@{settings.MUMBLE_URL}"
        ctx = self.get_context_data(
            temp_user=temp_user,
            link=link,
            connect_url=connect_url,
            mumble=settings.MUMBLE_URL,
        )
        return self.render_to_response(ctx)

    def link_sso(self, token, link):
        character: EveCharacter = EveCharacter.objects.get_character_by_id(
            token.character_id
        ) or EveCharacter.objects.create_character(token.character_id)

        formatted_name = NameFormatter(
            MumbleService(),
            PseudoUser(username=character.character_name, main_character=character),
        ).format_name()
        display_name = f"{app_settings.MUMBLE_TEMPS_SSO_PREFIX}{formatted_name}"
        return self.create_temp_user(display_name)


@method_decorator(permission_required("mumbletemps.create_new_links"), name="dispatch")
class DeleteTempLink(generic.DeleteView):
    model = TempLink
    slug_field = "link_ref"
    slug_url_kwarg = "link_ref"
    success_url = reverse_lazy("mumbletemps:index")
    queryset = TempLink.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f"Deleted Token {self.object.link_ref}")
        return super().delete(request)
