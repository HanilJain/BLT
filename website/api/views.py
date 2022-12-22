from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Sum
from django.contrib.auth.models import AnonymousUser

from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from website.models import (
    Issue,
    Domain,
)
from website.serializers import (
    IssueSerializer,
    UserProfileSerializer,
    DomainSerializer,
)

from website.models import (
    UserProfile,
    User,
    Points,
    IssueScreenshot
)


# API's


class UserIssueViewSet(viewsets.ModelViewSet):
    """
    User Issue Model View Set
    """

    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("user__username", "user__id")
    http_method_names = ["get", "post", "head"]


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    User Profile View Set
    """

    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("id", "user__id", "user__username")
    http_method_names = ["get", "post", "head"]

class DomainViewSet(viewsets.ModelViewSet):
    """
    Domain View Set
    """

    serializer_class = DomainSerializer
    queryset = Domain.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ("url", "name")
    http_method_names = ["get", "post", "head"]


class IssueViewSet(viewsets.ModelViewSet):
    """
    Issue View Set
    """

    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("url", "description", "user__id")
    http_method_names = ["get", "post", "head"]

    def get_issue_info(self,request,issue):
        
        if issue == None:
            return {}

        screenshots = [
            # replacing space with url space notation
            screenshot["image"].replace(" ","%20")
            for screenshot in 
            issue.screenshots.values("image").all()
        ] + ( [issue.screenshot.url] if issue.screenshot else [] )


        upvotes = issue.upvoted.all().__len__()
        flags = issue.flaged.all().__len__()
        upvotted = False
        flagged = False

        if type(request.user) != AnonymousUser:

            upvotted = bool(request.user.userprofile.issue_upvoted.filter(id=issue.id).first())
            flagged = bool(request.user.userprofile.issue_flaged.filter(id=issue.id).first())          

        return {
            **Issue.objects.values().filter(id=issue.id).first(),
            "upvotes": upvotes,
            "flags": flags,
            "upvotted": upvotted,
            "flagged": flagged,
            "screenshots": screenshots
        }


    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is None:
            return Response(issues)
            
        issues = []
        for issue in page:
            issues.append(self.get_issue_info(request,issue))

        return self.get_paginated_response(issues)


    def retrieve(self, request, pk,*args, **kwargs):

        issue = Issue.objects.filter(id=pk).first()
        return Response(self.get_issue_info(request,issue))

class LikeIssueApiView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,id,format=None,*args, **kwargs):
        return Response({
            "likes":UserProfile.objects.filter(issue_upvoted__id=id).count(),
        })
    
    def post(self,request,id,format=None,*args,**kwargs):

        issue = Issue.objects.get(id=id)
        userprof = UserProfile.objects.get(user=request.user)
        if userprof in UserProfile.objects.filter(issue_upvoted=issue):
            userprof.issue_upvoted.remove(issue)
            userprof.save()
            return Response({"issue":"unliked"})
        else:
            userprof.issue_upvoted.add(issue)
            userprof.save()
            
            liked_user = issue.user
            liker_user = request.user
            issue_pk = issue.pk

            if liked_user:

                msg_plain = render_to_string(
                    "email/issue_liked.txt",
                    {
                        "liker_user": liker_user.username,
                        "liked_user": liked_user.username,
                        "issue_pk": issue_pk,
                    },
                )
                msg_html = render_to_string(
                    "email/issue_liked.txt",
                    {
                        "liker_user": liker_user.username,
                        "liked_user": liked_user.username,
                        "issue_pk": issue_pk,
                    },
                )

                send_mail(
                    "Your issue got an upvote!!",
                    msg_plain,
                    "Bugheist <support@bugheist.com>",
                    [liked_user.email],
                    html_message=msg_html,
                )

            return Response({"issue":"liked"})

class FlagIssueApiView(APIView):
    '''
        api for Issue like,flag and bookmark
    '''

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,id,format=None,*args, **kwargs):
        return Response({
            "flags":UserProfile.objects.filter(issue_flaged__id=id).count(),
        })
    
    def post(self,request,id,format=None,*args,**kwargs):

        
        issue = Issue.objects.get(id=id)
        userprof = UserProfile.objects.get(user=request.user)
        if userprof in UserProfile.objects.filter(issue_flaged=issue):
            userprof.issue_flaged.remove(issue)
            userprof.save()
            return Response({"issue":"unflagged"})
        else:
            userprof.issue_flaged.add(issue)
            userprof.save()
            return Response({"issue":"flagged"})



class UserScoreApiView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,id,format=None,*args, **kwargs):
        total_score = Points.objects.filter(user__id=id).annotate(total_score=Sum('score'))

        return Response({"total_score":total_score})