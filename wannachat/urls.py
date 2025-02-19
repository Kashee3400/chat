from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from wannachat import views


urlpatterns = [
    path('management/', admin.site.urls),

    path('', views.HomeView.as_view(), name='home'),
    path(
        'change-country/', views.ChangeCountryView.as_view(),
        name='change_country'
    ),
    path('faq/', views.FAQPageView.as_view(), name='faq'),
    path('tos/', views.TOSPageView.as_view(), name='tos'),
    path('chat-rules/', views.ChatRulesPageView.as_view(), name='chat_rules'),
    path(
        'safety-tips/', views.SafetyTipsPageView.as_view(), name='safety_tips'
    ),
    path(
        'privacy-policy/', views.PrivacyPolicyPageView.as_view(),
        name='privacy_policy'
    ),
    path(
        'cookie-policy/', views.CookiePolicyPageView.as_view(),
        name='cookie_policy'
    ),
    path(
        'cookie-settings/', views.CookieSettingsPageView.as_view(),
        name='cookie_settings'
    ),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
    path('find-friend/', views.FindFriendView.as_view(), name='find_friend'),

    path('auth/', include('customauth.urls')),
    path('chatroom/', include('chatroom.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# serve media files in development environment --------------------------------
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
