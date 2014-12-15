import argparse
import logging
import os
from shutil import copytree, rmtree
from subprocess import Popen, PIPE

try:
    from venv import create as create_venv
    VENV_CREATE_KWARGS = {'symlinks': True}
except ImportError:
    from virtualenv import create_environment as create_venv
    VENV_CREATE_KWARGS = {'symlink': True}

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from . import VERSION


DIR_CURRENT = os.getcwd()
DJANGO_DEFAULT_VERSION = '1.7'
APPS_DIRNAME = 'apps'
VENVS_DIRNAME = 'venvs'


MANAGE_PY = '''
# This file is created automatically by django-dev.
# Do not try to edit it. All changes manually done will be lost.
import os
import sys


if __name__ == '__main__':
    #PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))
    sys.path = ['%(apps_path)s'] + sys.path

    try:
        import south
        south = ('south',)
    except:
        south = ()

    from django.conf import settings, global_settings
    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    )
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=INSTALLED_APPS + south + ('%(apps_available)s',),
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}},
            MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES,  # Prevents Django 1.7 warning.
            SOUTH_MIGRATION_MODULES = {%(south_migration_modules)s}
        )

    try:  # Django 1.7 +
        from django import setup
        setup()
    except ImportError:
        pass


    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'''


class DjangoDevException(Exception):
    """Exception class used by django-dev."""


class DevTools(object):

    def __init__(self, log_level=None):
        self.workshop_path = DIR_CURRENT
        self.apps_path = os.path.join(self.workshop_path, APPS_DIRNAME)
        self.venvs_path = os.path.join(self.workshop_path, VENVS_DIRNAME)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.configure_logging(log_level)

    def configure_logging(self, verbosity_lvl=None, format='DJANGO DEV %(levelname)s: %(message)s'):
        """Switches on logging at a given level.

        :param verbosity_lvl:
        :param format:

        """
        if not verbosity_lvl:
            verbosity_lvl = logging.INFO
        logging.basicConfig(format=format)
        self.logger.setLevel(verbosity_lvl)

    def _run_shell_command(self, command, pipe_it=True):
        """Runs the given shell command.

        :param command:
        :return: bool Status
        """
        stdout = None
        if pipe_it:
            stdout = PIPE
        self.logger.debug('Executing shell command: %s' % command)
        return not bool(Popen(command, shell=True, stdout=stdout).wait())

    def _get_venv_path(self, dj_version):
        """Returns virtual env directory path (named after Django version).

        :param str dj_version:
        :rtype: str
        :return: path
        """
        return os.path.join(self.venvs_path, dj_version)

    def _get_app_path(self, app_name):
        """Returns application directory path for a given app name.

        :param str app_name:
        :return: path
        """
        return os.path.join(self.apps_path, app_name)

    def _get_manage_py_path(self):
        """Returns a path to manage.py file.

        :rtype: str
        :return: path
        """
        return os.path.join(self.workshop_path, 'manage.py')

    def run_manage_command(self, command, venv_path, verbose=True):
        """Runs a given Django manage command in a given virtual environment.

        :param str command:
        :param str venv_path:
        :param bool verbose:
        """
        self.logger.debug('Running manage command `%s` for `%s` ...' % (command, venv_path))
        self._run_shell_command('. %s/bin/activate && python %s %s' % (venv_path, self._get_manage_py_path(), command), pipe_it=(not verbose))

    def venv_install(self, package_name, venv_path):
        """Installs a given python package into a given virtual environment.

        :param str package_name:
        :param str venv_path:
        """
        self.logger.debug('Installing `%s` into `%s` ...' % (package_name, venv_path))
        self._run_shell_command('. %s/bin/activate && pip install -U %s' % (venv_path, package_name))

    def make_venv(self, dj_version):
        """Creates a virtual environment for a given Django version.

        :param str dj_version:
        :rtype: str
        :return: path to created virtual env
        """
        venv_path = self._get_venv_path(dj_version)
        self.logger.info('Creating virtual environment for Django %s ...' % dj_version)
        try:
            create_venv(venv_path, **VENV_CREATE_KWARGS)
        except ValueError:
            self.logger.warning('Virtual environment directory already exists. Skipped.')
        self.venv_install('django==%s' % dj_version, venv_path)
        return venv_path

    def make_apps_dir(self):
        """Creates an empty directory for symlinks to Django applications.

        :rtype: str
        :return: created directory path
        """
        self.logger.info('Creating a directory for symlinks to your Django applications `%s` ...' % self.apps_path)
        try:
            os.mkdir(self.apps_path)
        except OSError:
            pass  # Already exists.
        return self.apps_path

    def dispatch_op(self, op_name, args_dict):
        """Dispatches an operation requested.

        :param str op_name:
        :param dict args_dict:
        """
        self.logger.debug('Requested `%s` command with `%s` args.' % (op_name, args_dict))
        method = getattr(self, 'op_%s' % op_name, None)
        if method is None:
            error_str = '`%s` command is not supported.' % op_name
            self.logger.error(error_str)
            raise DjangoDevException(error_str)
        method(**args_dict)
        self.logger.info('Done.')

    def get_venvs(self):
        """Returns a list of names of available virtual environments.

        :raises: DjangoDevException on errors
        :rtype: list
        :return: list of names
        """

        def raise_():
            error_str = 'Virtual environments are not created. Please run `bootstrap` command.'
            self.logger.error(error_str)
            raise DjangoDevException(error_str)

        if not os.path.exists(self.venvs_path):
            raise_()
        venvs = os.listdir(self.venvs_path)
        if not venvs:
            raise_()

        venvs.sort()
        return venvs

    def get_apps(self, only=None):
        """Returns a list of names of available Django applications,
        Optionally filters it using `only`.

        :param list|None only: a list on apps names to to filter all available apps against
        :raises: DjangoDevException on errors
        :rtype: list
        :return: list of apps names
        """
        if not os.path.exists(self.apps_path):
            error_str = 'It seems that this directory does not contain django-dev project. ' \
                        'Use `bootstrap` command to create project in the current directory.'
            self.logger.error(error_str)
            raise DjangoDevException(error_str)

        apps = os.listdir(self.apps_path)

        if not apps:
            error_str = 'Applications directory is empty. ' \
                        'Please symlink your apps (and other apps that you apps depend upon) into %s' % self.apps_path
            self.logger.error(error_str)
            raise DjangoDevException(error_str)

        apps.sort()
        if only is None:
            self.create_manage_py(apps)
            return apps

        diff = set(only).difference(apps)
        if diff:
            error_str = 'The following apps are not found: `%s`.' % ('`, `'.join(diff))
            self.logger.error(error_str)
            raise DjangoDevException(error_str)

        self.create_manage_py(apps)

        return [name for name in apps if name in only]

    def create_manage_py(self, apps):
        """Creates manage.py file, with a given list of installed apps.

        :param list apps:
        """
        self.logger.debug('Creating manage.py ...')
        with open(self._get_manage_py_path(), mode='w') as f:
            south_migration_modules = []
            for app in apps:
                south_migration_modules.append("'%(app)s': '%(app)s.south_migrations'" % {'app': app})

            f.write(MANAGE_PY % {
                'apps_available': "', '".join(apps),
                'apps_path': self.apps_path,
                'south_migration_modules': ", ".join(south_migration_modules)


            })

    def op_list_venvs(self):
        """Prints out and returns a list of known virtual environments.

        :rtype: list
        :return: list of virtual environments
        """
        self.logger.info('Listing known virtual environments ...')
        venvs = self.get_venvs()
        for venv in venvs:
            self.logger.info('Found `%s`' % venv)
        else:
            self.logger.info('No virtual environments found in `%s` directory.' % VENVS_DIRNAME)
        return venvs

    def op_list_apps(self):
        """Prints out and returns a list of known applications.

        :rtype: list
        :return: list of applications
        """
        self.logger.info('Listing known applications ...')
        apps = self.get_apps()
        for app in apps:
            self.logger.info('Found `%s`' % app)
        else:
            self.logger.info('\nDONE. No applications found in `%s` directory.\n' % APPS_DIRNAME)
        return apps

    def op_bootstrap(self):
        """Bootstraps django-dev by creating required directory structure."""
        self.logger.info('Bootstrapping django-dev directory structure in current directory ...')
        self.make_venv(DJANGO_DEFAULT_VERSION)
        venv_path = self.make_venv('1.6.5')
        self.venv_install('south==1.0.1', venv_path)
        apps_dir = self.make_apps_dir()
        self.logger.info('Now you may symlink (ln -s) your apps '
                         '(and other apps that you apps depend upon) into %s' % apps_dir)

    def _make_dirs(self, path):
        """Creates every directory in path as needed. Fails silently.

        :param str path:
        :rtype: bool
        :return: True if no exceptions raised; otherwise - False.
        """
        try:
            os.makedirs(path)
            return True
        except OSError:  # Probably already exists.
            pass
        return False

    def op_make_trans(self, locales=None, apps=None):
        """Generates/updates localization (.po, .mo) files for applications.

        :param list|None locales: Locales to generate files for. If `None` all available locales in apps are updated.
        :param list|None apps: Target applications filter. If `None` all available apps are processed.
        """
        self.logger.info('Making translations ...')
        apps = self.get_apps(only=apps)
        self.get_venvs()  # Sentinel.
        venv_path = self._get_venv_path(DJANGO_DEFAULT_VERSION)
        if locales is None:
            locales = []

        for app_name in apps:
            self.logger.info('For `%s` application ...' % app_name)
            app_path = self._get_app_path(app_name)
            locales_path = os.path.join(app_path, 'locale')

            if not locales and os.path.exists(locales_path):  # Getting all existing locales.
                locales = os.listdir(locales_path)

            for lang in locales:
                self.logger.info('Working on `%s` locale ...' % lang)
                locale_path = os.path.join(locales_path, '%s/LC_MESSAGES' % lang)
                self._make_dirs(locale_path)
                old_wd = os.getcwd()
                os.chdir(app_path)
                self.run_manage_command('makemessages -l %s' % lang, venv_path)
                self.run_manage_command('compilemessages -l %s' % lang, venv_path)
                os.chdir(old_wd)

    def op_add_migrations(self, apps=None, relocate_south=False):
        self.logger.info('Making migrations ...')
        apps = self.get_apps(only=apps)
        venvs = self.get_venvs()  # Sentinel.

        default_venv_path = self._get_venv_path(DJANGO_DEFAULT_VERSION)

        def fix_migrations(path):
            """Fixes buggy migrations created with `makemigrations` using Py2.
            See: https://code.djangoproject.com/ticket/23455

            :param path:
            :return:
            """
            self.logger.info('Fixing migrations ...')
            for file in os.listdir(path):
                if os.path.splitext(file)[1] == '.py':
                    with open(os.path.join(path, file), 'r+') as f:
                        contents = f.read()
                        f.seek(0)
                        f.write(contents.replace("=b'", "='"))
                        f.truncate()

        for venv in venvs:
            venv_path = self._get_venv_path(venv)

            for app_name in apps:
                app_path = self._get_app_path(app_name)
                PATH_SOUTH = os.path.join(app_path, 'south_migrations')
                PATH_BUILTIN = os.path.join(app_path, 'migrations')
                south_exists = os.path.exists(PATH_SOUTH)

                self.logger.info('For `%s` application in `%s` ...' % (app_name, venv_path))

                if relocate_south and not south_exists and os.path.exists(PATH_BUILTIN):  # Foolproof.
                    self.logger.info('Relocating South migrations into %s ...' % PATH_SOUTH)
                    copytree(PATH_BUILTIN, PATH_SOUTH)
                    rmtree(PATH_BUILTIN)
                    south_exists = True

                # Add migrations for both.
                if venv_path == default_venv_path:  # Django with migrations built-in (1.7+)
                    self.run_manage_command('makemigrations %s' % app_name, venv_path, verbose=False)
                else:
                    flag = '--auto'
                    if not south_exists:
                        flag = '--init'
                    self.run_manage_command('schemamigration %s %s' % (app_name, flag), venv_path, verbose=False)

                fix_migrations(PATH_BUILTIN)


def main():
    arg_parser = argparse.ArgumentParser(prog='django-dev', description='Tools to facilitate application development for Django', version='.'.join(map(str, VERSION)))

    arg_parser.add_argument('--debug', help='Show debug messages while processing', action='store_true')

    arg_parser_apps = argparse.ArgumentParser(add_help=False)
    arg_parser_apps.add_argument('--apps', nargs='+', help='Whitespace-separated list of applications names. Example: sitecats, siteflags.')

    sub_parsers = arg_parser.add_subparsers(dest='subparser_name')
    sub_parsers.add_parser('bootstrap', help='Creates a basic django-dev directory structure in a current directory.')
    sub_parsers.add_parser('list_apps', help='Prints out currently available applications.')
    sub_parsers.add_parser('list_venvs', help='Prints out currently available virtual environments.')

    sub_parser_add_migrations = sub_parsers.add_parser('add_migrations', help='Adds both South and Django 1.7+ migrations for apps.', parents=[arg_parser_apps])
    sub_parser_add_migrations.add_argument('--relocate_south', help='Flag to relocate old South migrations from `migrations` into `south_migrations` folder.', action='store_true')

    sub_parser_make_trans = sub_parsers.add_parser('make_trans', help='Creates translation (.po, .mo) files for the given locales.', parents=[arg_parser_apps])
    sub_parser_make_trans.add_argument('locales', nargs='*', help='Locales identifiers to make localization files for. Whitespace-separated values are allowed. Example: ru en.')

    parsed_args = arg_parser.parse_args()
    parsed_args = vars(parsed_args)  # Convert args to dict

    log_level = None
    if parsed_args['debug']:
        log_level = logging.DEBUG
    del parsed_args['debug']

    dt = DevTools(log_level=log_level)

    target_subparser = parsed_args['subparser_name']
    del parsed_args['subparser_name']

    try:
        dt.dispatch_op(target_subparser, parsed_args)
    except DjangoDevException:
        pass  # This will be logged in into stdout.
