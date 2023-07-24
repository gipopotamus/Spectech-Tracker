from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(reverse('login')):
            # Если пользователь не залогинен и не находится на странице логина,
            # перенаправляем на страницу логина
            return HttpResponseRedirect(reverse('login'))  # Замените 'login' на URL вашей страницы логина
        return self.get_response(request)
