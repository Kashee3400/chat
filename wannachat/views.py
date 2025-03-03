from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from chatroom.models import Category, Country, Contact
from chatroom.forms import ContactForm
from customauth.models import Profile

class HomeView(View):
    """ Home view displaying categories based on selected country """
    template_name = 'home/home.html'

    def _get_country_from_session(self, request):
        """Retrieve the country from the session or fallback to default."""
        country_name = request.session.get('country')
        if country_name:
            return Country.objects.filter(name=country_name).first()
        return Country.objects.filter(pk=1).first()

    def _get_category_list(self, country):
        """Retrieve categories based on country selection."""
        return Category.objects.filter(
            Q(Q(country=country) & Q(is_active=True)) | Q(country__slug='world')
        ).order_by('ordering')

    def get(self, request, *args, **kwargs):
        country = self._get_country_from_session(request)
        category_list = self._get_category_list(country) if country else None

        context = {
            'category_list': category_list,
            'selected_country': country,
        }
        return render(request, self.template_name, context)


class ChangeCountryView(View):
    """ Handles country change and updates category listing """
    template_name = 'home/rooms.html'

    def _get_country_from_request(self, request):
        """Retrieve country from request parameters and store it in session."""
        country_name = request.GET.get('country')
        if country_name:
            request.session['country'] = country_name
        return Country.objects.filter(name=country_name).first()

    def get(self, request, *args, **kwargs):
        country = self._get_country_from_request(request) or Country.objects.filter(pk=1).first()
        category_list = Category.objects.filter(
            Q(Q(country=country) & Q(is_active=True)) | Q(country__slug='world')
        ).order_by('ordering') if country else None

        context = {
            'category_list': category_list,
            'selected_country': country,
        }
        return render(request, self.template_name, context)


class FAQPageView(TemplateView):
    template_name = 'home/faq.html'


class TOSPageView(TemplateView):
    template_name = 'home/tos.html'


class ChatRulesPageView(TemplateView):
    template_name = 'home/chat_rules.html'


class SafetyTipsPageView(TemplateView):
    template_name = 'home/safety_tips.html'


class PrivacyPolicyPageView(TemplateView):
    template_name = 'home/privacy_policy.html'


class CookiePolicyPageView(TemplateView):
    template_name = 'home/cookie_policy.html'


class CookieSettingsPageView(TemplateView):
    template_name = 'home/cookie_settings.html'


class ContactPageView(View):
    template_name = 'home/contact.html'
    model = Contact
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message submitted successfully.')
        context = {
            'form': form,
        }
        return render(request, self.template_name, context)


class FindFriendView(LoginRequiredMixin, View):
    template_name = 'home/find-friend.html'
    login_url = "/auth/login/"

    def get(self, request, *args, **kwargs):
        country = Country.objects.all()
        context = {
            'country_list': country,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        country = request.POST.get('country')
        state = request.POST.get('state')
        gender = request.POST.get('gender')
        print(name, country, state, gender)
        # friends = Profile.objects.filter(
        #     Q(user__username__icontains=name) | Q(name__icontains=name) | Q(
        #         gender=gender
        #     ) | Q(country__pk=country) | Q(state__pk=state)
        # )
        friends = Profile.objects.all()
        if name:
            friends = friends.filter(
                Q(user__username__icontains=name) | Q(name__icontains=name)
            )
        if gender:
            friends = friends.filter(gender=gender)
        if country:
            friends = friends.filter(country__pk=country)
        if state:
            friends = friends.filter(state__pk=state)
        friends = friends.exclude(user__email=request.user.email)
        friends = friends.exclude(user__is_superuser=True)
        print(friends)
        country_list = Country.objects.all()
        context = {
            'country_list': country_list,
            'friends': friends,
        }
        return render(request, self.template_name, context)
