django-dev
==========
https://github.com/idlesign/django-dev

.. image:: https://img.shields.io/pypi/v/django-dev.svg
    :target: https://pypi.python.org/pypi/django-dev

.. image:: https://img.shields.io/pypi/dm/django-dev.svg
    :target: https://pypi.python.org/pypi/django-dev

.. image:: https://img.shields.io/pypi/l/django-dev.svg
    :target: https://pypi.python.org/pypi/django-dev


Description
-----------

*Tools to facilitate application development for Django*

Console utility for those who have more than one Django reusable application to maintain.

It allows certain actions to be done in batch mode over all you apps.


Supported commands:

* **bootstrap**

* **add_migrations**

* **make_trans**

* **list_apps**

* **list_venvs**

* **install_package**



Requirements
------------

1. Python 2.7+, 3.2+
2. Python `virtualenv` package (or just Python 3.3+).


How to start
------------

1. Make a new directory, where you want your workspace to be, and step into it;

2. Run ``> django-dev bootstrap`` to create basic directory structure;

3. Symlink your apps into ``apps`` directory (was created by step 2 in your current directory).

    Example:

    ``ln -s /home/idle/dev/django-sitetree/sitetree /home/idle/dev/dj_workspace/apps/sitetree``

    Notice, that symlinked is a directory containing *models.py* (not *setup.py*).



Making both South and Django 1.7+ migrations
--------------------------------------------

Use **add_migrations** command.

* Relocate old South migrations into *south_migrations* and create new migrations in *migrations*:

  ``> django-dev add_migrations --relocate_south``

* Create/update migrations both for South and Django 1.7:

  ``> django-dev add_migrations``

* Create/update migrations for certain apps:

  ``> django-dev add_migrations --apps sitecats siteflags``



Updating translation files
--------------------------

Use **make_trans** command.

* Update existing .mo and .po files for every locale available in app:

  ``> django-dev make_trans``

* Update/create .mo and .po files for certain locales:

  ``> django-dev make_trans ru en``

* Update/create .mo and .po files for certain apps:

  ``> django-dev make_trans ru --apps sitetree sitegate``



Get involved into django-dev
----------------------------

**Submit issues.** If you spotted something weird in application behavior or want to propose a feature you can do that at https://github.com/idlesign/django-dev/issues

**Write code.** If you are eager to participate in application development, fork it at https://github.com/idlesign/django-dev, write your code, whether it should be a bugfix or a feature implementation, and make a pull request right from the forked project page.

**Spread the word.** If you have some tips and tricks or any other words in mind that you think might be of interest for the others — publish it.
