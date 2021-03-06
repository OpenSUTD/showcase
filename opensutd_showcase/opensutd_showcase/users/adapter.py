from django.conf import settings
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from allauth.exceptions import ImmediateHttpResponse

from website.models import User

class CustomGithubAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        try:
            user = User.objects.get(username=sociallogin.user.username)
            sociallogin.connect(request, user)
            raise ImmediateHttpResponse("Account already exists!!")
        except Exception as e:
            print(e)

    def populate_user(self, request, sociallogin, data):
        user = sociallogin.user
        #print(data)
        user.username = data["username"].lower()
        if (data["name"] is not None and len(data["name"])>4):
            user.display_name = data["name"]
        else:
            user.display_name = data["username"]
            
