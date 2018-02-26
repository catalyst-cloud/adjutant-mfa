Adjutant MFA Plugin
====================

Installation Instructions
--------------------------

Install the package into the virtual environment that you have installed
adjutant into.

Edit the ``conf.yaml`` file to enable this plugin.

To ``ADDITIONAL_APPS`` add:

.. code-block:: yaml

    - mfa_actions
    - mfa_views

In ``ACTIVE_TASKVIEWS`` replace ``UserList`` with ``UserListMFA``, and add
``EditMFA``.

.. code-block:: yaml

    - UserListMFA
    - EditMFA

And to ``TASK_SETTINGS`` add:

.. code-block:: yaml

    edit_mfa:
        cloud_name: OpenStack
        duplicate_policy: cancel
        emails:
            token: null

``cloud_name`` will show up on the TOTP provisioning uris, and in the user's
authenticator app.
