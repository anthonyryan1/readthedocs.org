"""
This is a helper to debug issues with projects on the server more easily
locally. It allows you to import projects based on the data that the public API
provides.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
import json
import slumber

from django.contrib.auth.models import User
from ...models import Project


class Command(BaseCommand):
    help = (
        "Retrieves the data of a project from readthedocs.org's API and puts "
        "it into the local database. This is mostly useful for debugging "
        "issues with projects on the live site."
    )

    def add_arguments(self, parser):
        parser.add_argument('project_slug', nargs='+', type=str)

    def handle(self, *args, **options):
        api = slumber.API(base_url='http://readthedocs.org/api/v1/')
        user1 = User.objects.order_by('pk').first()

        for slug in options['project_slug']:
            self.stdout.write('Importing {slug} ...'.format(slug=slug))

            project_data = api.project.get(slug=slug)
            try:
                project_data = project_data['objects'][0]
            except (KeyError, IndexError):
                self.stderr.write(
                    'Cannot find {slug} in API. Response was:\n{response}'
                    .format(
                        slug=slug,
                        response=json.dumps(project_data)))

            try:
                project = Project.objects.get(slug=slug)
            except Project.DoesNotExist:
                project = Project(slug=slug)

            project.python_interpreter
            copy_attributes = (
                'pub_date',
                'modified_date',
                'name',
                'description',
                'repo',
                'repo_type',
                'project_url',
                'canonical_url',
                'version',
                'copyright',
                'theme',
                'suffix',
                'single_version',
                'default_version',
                'default_branch',
                'requirements_file',
                'documentation_type',
                'allow_comments',
                'comment_moderation',
                # 'analytics_code' is left out on purpose.
                'enable_epub_build',
                'enable_pdf_build',
                'conf_py_file',
                'skip',
                'mirror',
                'use_virtualenv',
                'python_interpreter',
                'use_system_packages',
                'django_packages_url',
                'privacy_level',
                'version_privacy_level',
                'language',
                'num_major',
                'num_minor',
                'num_point',
            )

            for attribute in copy_attributes:
                setattr(project, attribute, project_data[attribute])
            project.python_interpreter
            project.user = user1
            project.save()
            if user1:
                project.users.add(user1)

            call_command('update_repos', project.slug, version='all')
