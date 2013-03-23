"""
Test code for ansible commander.

(C) 2013 AnsibleWorks <michael@ansibleworks.com>
"""


import datetime
import json

from django.contrib.auth.models import User as DjangoUser
import django.test
from django.test.client import Client
from lib.main.models import *


class BaseTest(django.test.TestCase):

    def make_user(self, username, password, super_user=False):
        django_user = None
        if super_user:
            django_user = DjangoUser.objects.create_superuser(username, "%s@example.com", password)
        else:
            django_user = DjangoUser.objects.create_user(username, "%s@example.com", password)
        return django_user

    def make_organizations(self, created_by, count=1):
        results = []
        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            results.append(Organization.objects.create(
                name="org%s-%s" % (x, self.object_ctr), description="org%s" % x, created_by=created_by
            ))
        return results

    def make_projects(self, created_by, count=1):
        results = []
        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            results.append(Project.objects.create(
                name="proj%s-%s" % (x, self.object_ctr), description="proj%s" % x, scm_type='git', 
                default_playbook='foo.yml', local_repository='/checkout', created_by=created_by
            ))
        return results

    def check_pagination_and_size(self, data, desired_count, previous=None, next=None):
        self.assertEquals(data['previous'], previous)
        self.assertEquals(data['next'], next)

    def setup_users(self):
        # Create a user.
        self.super_username  = 'admin'
        self.super_password  = 'admin'
        self.normal_username = 'normal'
        self.normal_password = 'normal'
        self.other_username  = 'other'
        self.other_password  = 'other'

        self.super_django_user  = self.make_user(self.super_username,  self.super_password, super_user=True)
        self.normal_django_user = self.make_user(self.normal_username, self.normal_password, super_user=False)
        self.other_django_user  = self.make_user(self.other_username,  self.other_password, super_user=False)

    def get_super_credentials(self):
        return (self.super_username, self.super_password)

    def get_normal_credentials(self):
        return (self.normal_username, self.normal_password)

    def get_other_credentials(self):
        return (self.other_username, self.other_password)

    def get_invalid_credentials(self):
        return ('random', 'combination')
        
    def _generic_rest(self, url, data=None, expect=204, auth=None, method=None):
        assert method is not None
        method = method.lower()
        if method not in [ 'get', 'delete' ]:
            assert data is not None
        client = Client()
        if auth:
           client.login(username=auth[0], password=auth[1])
        method = getattr(client,method)
        response = None
        if data is not None:
            response = method(url, json.dumps(data), 'application/json')
        else:
            response = method(url)

        if response.status_code == 500 and expect != 500:
            assert False, "Failed: %s" % response.content
        if expect is not None:
            assert response.status_code == expect, "expected status %s, got %s for url=%s as auth=%s: %s" % (expect, response.status_code, url, auth, response.content)
        if response.status_code not in [ 202, 204, 400, 405, 409 ]:
            # no JSON responses in these at least for now, 400/409 should probably return some (FIXME)
            return json.loads(response.content)
        else:
            return None
 
    def get(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='get')

    def post(self, url, data, expect=204, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='post')

    def put(self, url, data, expect=200, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='put')

    def delete(self, url, expect=201, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='delete')

    def get_urls(self, collection_url, auth=None):
        # TODO: this test helper function doesn't support pagination
        data = self.get(collection_url, expect=200, auth=auth)
        return [item['url'] for item in data['results']]
    
