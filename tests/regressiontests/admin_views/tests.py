
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import LOGIN_FORM_KEY, _encode_post_data

# local test models
from models import Article, CustomArticle

def get_perm(Model, perm):
    """Return the permission object, for the Model"""
    ct = ContentType.objects.get_for_model(Model)
    return Permission.objects.get(content_type=ct,codename=perm)
    

class AdminViewPermissionsTest(TestCase):
    """Tests for Admin Views Permissions."""
    
    fixtures = ['admin-views-users.xml']
    
    def setUp(self):
        """Test setup."""
        # Setup permissions, for our users who can add, change, and delete. 
        # We can't put this into the fixture, because the content type id
        # and the permission id could be different on each run of the test.
        
        opts = Article._meta
        
        # User who can add Articles
        add_user = User.objects.get(username='adduser')
        add_user.user_permissions.add(get_perm(Article,
            opts.get_add_permission()))
        
        # User who can change Articles
        change_user = User.objects.get(username='changeuser')
        change_user.user_permissions.add(get_perm(Article,
            opts.get_change_permission()))
        
        # User who can delete Articles
        delete_user = User.objects.get(username='deleteuser')
        delete_user.user_permissions.add(get_perm(Article,
            opts.get_delete_permission()))
        
        # login POST dicts
        self.super_login = {'post_data': _encode_post_data({}),
                     LOGIN_FORM_KEY: 1,
                     'username': 'super',
                     'password': 'secret'}
        self.adduser_login = {'post_data': _encode_post_data({}),
                     LOGIN_FORM_KEY: 1,
                     'username': 'adduser',
                     'password': 'secret'}
        self.changeuser_login = {'post_data': _encode_post_data({}),
                     LOGIN_FORM_KEY: 1,
                     'username': 'changeuser',
                     'password': 'secret'}
        self.deleteuser_login = {'post_data': _encode_post_data({}),
                     LOGIN_FORM_KEY: 1,
                     'username': 'deleteuser',
                     'password': 'secret'}
        self.joepublic_login = {'post_data': _encode_post_data({}),
                     LOGIN_FORM_KEY: 1,
                     'username': 'joepublic',
                     'password': 'secret'}
           
        
    def testLogin(self):
        """
        Make sure only staff members can log in.
        
        Successful posts to the login page will redirect to the orignal url.
        Unsuccessfull attempts will continue to render the login page with 
        a 200 status code.
        """
        # Super User
        request = self.client.get('/test_admin/admin/')
        self.failUnlessEqual(request.status_code, 200)
        login = self.client.post('/test_admin/admin/', self.super_login)
        self.assertRedirects(login, '/test_admin/admin/')
        self.assertFalse(login.context)
        self.client.get('/test_admin/admin/logout/')
        
        # Add User
        request = self.client.get('/test_admin/admin/')
        self.failUnlessEqual(request.status_code, 200)
        login = self.client.post('/test_admin/admin/', self.adduser_login)
        self.assertRedirects(login, '/test_admin/admin/')
        self.assertFalse(login.context)
        self.client.get('/test_admin/admin/logout/')
        
        # Change User
        request = self.client.get('/test_admin/admin/')
        self.failUnlessEqual(request.status_code, 200)
        login = self.client.post('/test_admin/admin/', self.changeuser_login)
        self.assertRedirects(login, '/test_admin/admin/')
        self.assertFalse(login.context)
        self.client.get('/test_admin/admin/logout/')
        
        # Delete User
        request = self.client.get('/test_admin/admin/')
        self.failUnlessEqual(request.status_code, 200)
        login = self.client.post('/test_admin/admin/', self.deleteuser_login)
        self.assertRedirects(login, '/test_admin/admin/')
        self.assertFalse(login.context)
        self.client.get('/test_admin/admin/logout/')
        
        # Regular User should not be able to login.
        request = self.client.get('/test_admin/admin/')
        self.failUnlessEqual(request.status_code, 200)
        login = self.client.post('/test_admin/admin/', self.joepublic_login)
        self.failUnlessEqual(login.status_code, 200)
        # Login.context is a list of context dicts we just need to check the first one.
        self.assert_(login.context[0].get('error_message'))
    
    def testAddView(self):
        """Test add view restricts access and actually adds items."""
        
        add_dict = {'content': '<p>great article</p>',
                    'date_0': '2008-03-18', 'date_1': '10:54:39'}
        
        # Change User should not have access to add articles
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.changeuser_login)
        request = self.client.get('/test_admin/admin/admin_views/article/add/')
        self.failUnlessEqual(request.status_code, 403)
        # Try POST just to make sure
        post = self.client.post('/test_admin/admin/admin_views/article/add/', add_dict)
        self.failUnlessEqual(post.status_code, 403)
        self.failUnlessEqual(Article.objects.all().count(), 1)
        self.client.get('/test_admin/admin/logout/')
        
        # Add user may login and POST to add view, then redirect to admin root
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.adduser_login)
        post = self.client.post('/test_admin/admin/admin_views/article/add/', add_dict)
        self.assertRedirects(post, '/test_admin/admin/')
        self.failUnlessEqual(Article.objects.all().count(), 2)
        self.client.get('/test_admin/admin/logout/')
        
        # Super can add too, but is redirected to the change list view
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.super_login)
        post = self.client.post('/test_admin/admin/admin_views/article/add/', add_dict)
        self.assertRedirects(post, '/test_admin/admin/admin_views/article/')
        self.failUnlessEqual(Article.objects.all().count(), 3)
        self.client.get('/test_admin/admin/logout/')
        
        # Check and make sure that if user expires, data still persists
        post = self.client.post('/test_admin/admin/admin_views/article/add/', add_dict)
        self.assertContains(post, 'Please log in again, because your session has expired.')
        self.super_login['post_data'] = _encode_post_data(add_dict)
        post = self.client.post('/test_admin/admin/admin_views/article/add/', self.super_login)
        self.assertRedirects(post, '/test_admin/admin/admin_views/article/')
        self.failUnlessEqual(Article.objects.all().count(), 4)
        self.client.get('/test_admin/admin/logout/')
        
    def testChangeView(self):
        """Change view should restrict access and allow users to edit items."""
        
        change_dict = {'content': '<p>edited article</p>',
                    'date_0': '2008-03-18', 'date_1': '10:54:39'}
        
        # add user shoud not be able to view the list of article or change any of them
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.adduser_login)
        request = self.client.get('/test_admin/admin/admin_views/article/')
        self.failUnlessEqual(request.status_code, 403)
        request = self.client.get('/test_admin/admin/admin_views/article/1/')
        self.failUnlessEqual(request.status_code, 403)
        post = self.client.post('/test_admin/admin/admin_views/article/1/', change_dict)
        self.failUnlessEqual(post.status_code, 403)
        self.client.get('/test_admin/admin/logout/')
        
        # change user can view all items and edit them
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.changeuser_login)
        request = self.client.get('/test_admin/admin/admin_views/article/')
        self.failUnlessEqual(request.status_code, 200)
        request = self.client.get('/test_admin/admin/admin_views/article/1/')
        self.failUnlessEqual(request.status_code, 200)
        post = self.client.post('/test_admin/admin/admin_views/article/1/', change_dict)
        self.assertRedirects(post, '/test_admin/admin/admin_views/article/')
        self.failUnlessEqual(Article.objects.get(pk=1).content, '<p>edited article</p>')
        self.client.get('/test_admin/admin/logout/')
        
    def testCustomModelAdminTemplates(self):
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.super_login)
        
        # Test custom change list template with custom extra context
        request = self.client.get('/test_admin/admin/admin_views/customarticle/')
        self.failUnlessEqual(request.status_code, 200)
        self.assert_("var hello = 'Hello!';" in request.content)
        self.assertTemplateUsed(request, 'custom_admin/change_list.html')
        
        # Test custom change form template
        request = self.client.get('/test_admin/admin/admin_views/customarticle/add/')
        self.assertTemplateUsed(request, 'custom_admin/change_form.html')
        
        # Add an article so we can test delete and history views
        post = self.client.post('/test_admin/admin/admin_views/customarticle/add/', {
            'content': '<p>great article</p>',
            'date_0': '2008-03-18',
            'date_1': '10:54:39'
        })
        self.assertRedirects(post, '/test_admin/admin/admin_views/customarticle/')
        self.failUnlessEqual(CustomArticle.objects.all().count(), 1)
        
        # Test custom delete and object history templates
        request = self.client.get('/test_admin/admin/admin_views/customarticle/1/delete/')
        self.assertTemplateUsed(request, 'custom_admin/delete_confirmation.html')
        request = self.client.get('/test_admin/admin/admin_views/customarticle/1/history/')
        self.assertTemplateUsed(request, 'custom_admin/object_history.html')
        
        self.client.get('/test_admin/admin/logout/')
        
    def testCustomAdminSiteTemplates(self):
        from django.contrib import admin
        self.assertEqual(admin.site.index_template, None)
        self.assertEqual(admin.site.login_template, None)
        
        self.client.get('/test_admin/admin/logout/')
        request = self.client.get('/test_admin/admin/')
        self.assertTemplateUsed(request, 'admin/login.html')
        self.client.post('/test_admin/admin/', self.changeuser_login)
        request = self.client.get('/test_admin/admin/')
        self.assertTemplateUsed(request, 'admin/index.html')
        
        self.client.get('/test_admin/admin/logout/')
        admin.site.login_template = 'custom_admin/login.html'
        admin.site.index_template = 'custom_admin/index.html'
        request = self.client.get('/test_admin/admin/')
        self.assertTemplateUsed(request, 'custom_admin/login.html')
        self.assert_('Hello from a custom login template' in request.content)
        self.client.post('/test_admin/admin/', self.changeuser_login)
        request = self.client.get('/test_admin/admin/')
        self.assertTemplateUsed(request, 'custom_admin/index.html')
        self.assert_('Hello from a custom index template' in request.content)
                
        # Finally, using monkey patching check we can inject custom_context arguments in to index
        original_index = admin.site.index
        def index(*args, **kwargs):
            kwargs['extra_context'] = {'foo': '*bar*'}
            return original_index(*args, **kwargs)
        admin.site.index = index
        request = self.client.get('/test_admin/admin/')
        self.assertTemplateUsed(request, 'custom_admin/index.html')
        self.assert_('Hello from a custom index template *bar*' in request.content)
        
        self.client.get('/test_admin/admin/logout/')
        del admin.site.index # Resets to using the original
        admin.site.login_template = None
        admin.site.index_template = None
    
    def testDeleteView(self):
        """Delete view should restrict access and actually delete items."""

        delete_dict = {'post': 'yes'}
        
        # add user shoud not be able to delete articles
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.adduser_login)
        request = self.client.get('/test_admin/admin/admin_views/article/1/delete/')
        self.failUnlessEqual(request.status_code, 403)
        post = self.client.post('/test_admin/admin/admin_views/article/1/delete/', delete_dict)
        self.failUnlessEqual(post.status_code, 403)
        self.failUnlessEqual(Article.objects.all().count(), 1)
        self.client.get('/test_admin/admin/logout/')
        
        # Delete user can delete
        self.client.get('/test_admin/admin/')
        self.client.post('/test_admin/admin/', self.deleteuser_login)
        request = self.client.get('/test_admin/admin/admin_views/article/1/delete/')
        self.failUnlessEqual(request.status_code, 200)
        post = self.client.post('/test_admin/admin/admin_views/article/1/delete/', delete_dict)
        # TODO: http://code.djangoproject.com/ticket/6819 or the next line fails
        self.assertRedirects(post, '/test_admin/admin/')
        self.failUnlessEqual(Article.objects.all().count(), 0)
        self.client.get('/test_admin/admin/logout/')
        