from django.urls import include, path
from rest_framework.routers import SimpleRouter, Route, DynamicRoute

from dj_rest_auth.viewsets import UserDetailsViewSet

from .urls import test_urlpatterns

class ViewSetTestRouter(SimpleRouter):
    """
    A custom router for viewset tests, giving it the same reverse URLs.
    """
    routes = [
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='rest_user_details',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        DynamicRoute(
            url=r'^{prefix}/{url_path}{trailing_slash}$',
            name='{url_name}',
            detail=False,
            initkwargs={}
        ),
    ]

    def get_default_basename(self, viewset):
      return ''

router = ViewSetTestRouter()
router.register(r'account', UserDetailsViewSet)

urlpatterns = test_urlpatterns + [
    path('', include(router.urls)),
]
