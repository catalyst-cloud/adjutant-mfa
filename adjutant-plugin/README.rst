Adjutant MFA Plugin
====================

Installation Instructions
--------------------------

Install the package into the virtual environment that you have installed
adjutant into.

Edit the conf.yaml file to enable this plugin.

To INSTALLED_APPS add:
.. code-block:: yaml

    - mfa_actions
    - mfa_views

And to TASK_SETTINGS add:
.. code-block:: yaml

    edit_mfa:
        duplicate_policy: cancel
        token: null
