===============================
Keystone MFA Plugin
===============================

This adds an authentication plugin to Keystone such that if the user
has a 'totp' type credential added to their account it will force them
to authenticate with both password and a valid TOTP code.

The TOTP code must be appended to the user's password when authenticating
for this to work.

e.g: If the user's password is 'password' and their current TOTP passcode is
123456 they would submit their whole password as 'password123456'.

It is advised that users enter their password + passcode combination once
and use it to generate a token to authenticate with during their workflow.

If the adjutant plugin is not in use TOTP can be directly enabled for a user
with this command.

.. code-block:: bash

  openstack credential create <user_id> <secret> --type totp

The adjutant plugin will allow users to manage their own MFA credentials, and
includes checks to prevent users from adding a credential they do not have
stored in a generator.

The password-totp plugin requires keystone V3, and it is recommended that you
disable Keystone v2 if possible, if not, see the section below about how to
selectively disable v2 for MFA enabled users.

This plugin works as a normal password plugin if no TOTP credentials are
present for user, otherwise expects totp passcode appended to the password.


Installation and setup
----------------------

To install the plugin into the current python environment:

.. code-block::

  python setup.py install

  or (if this ever gets published to pypi)

  pip install keystone-adjutant-mfa


Then in the auth section of the keystone.conf file add:

.. code-block::

  [auth]
  password = queens.password_totp

Then restart the keystone server.

There is a version of the plugin going back as far as Mitaka, with the Ocata
version also working for Pike, and the Queens version (currently) working for
Rocky.


Disabling Keystone v2 for MFA enabled users
-------------------------------------------

**NOTE: This part of the readme is is talking about Keystone code before
Ocata, and Ocata onwards is quite different for the V2 controller code, so
while the essence of this section is still valid, you will need to find Ocata+
appropriate variants yourself.**

If you have Keystone v2 enabled, then a user with MFA enabled can easily bypass
the MFA and authenticate with Keystone v2. V2 does not support MFA, nor will it
ever.

If you must have Keystone v2 enabled, then your only recourse is to selectively
edit the v2 code to explicitly deny auth to any users with MFA configured, and
instruct them to use v3.

Doing this at least is easy and require a couple of small changes to the v2
auth code.

In ``keystone/token/controllers.py`` you need to first include
``credential_api`` in the dependencies for the auth class:

This section:

.. code-block:: python

  @dependency.requires('assignment_api', 'catalog_api', 'identity_api',
                     'resource_api', 'role_api', 'token_provider_api',
                     'trust_api')
  class Auth(controller.V2Controller):

Becomes:

.. code-block:: python

  @dependency.requires('assignment_api', 'catalog_api', 'identity_api',
                     'resource_api', 'role_api', 'token_provider_api',
                     'trust_api', 'credential_api')
  class Auth(controller.V2Controller):

Then in the ``_authenticate_local`` function you need to add a check to raise
an error in the event that a user has MFA enabled:

This section (roughly around line 299):

.. code-block:: python

  try:
    user_ref = self.identity_api.authenticate(
        context,
        user_id=user_id,
        password=password)
  except AssertionError as e:
    raise exception.Unauthorized(e.args[0])

Becomes:

.. code-block:: python

  # NOTE: Block MFA enabled users from authenticating with v2
  credentials = self.credential_api.list_credentials_for_user(user_id)
  credentials = [cred for cred in credentials if cred['type'] == 'totp']
  if credentials:
    raise exception.Unauthorized("Must authenticate with v3.")

  # now auth normally
  try:
    user_ref = self.identity_api.authenticate(
        context,
        user_id=user_id,
        password=password)
  except AssertionError as e:
    raise exception.Unauthorized(e.args[0])

**WARNING: Be very careful editing this code, and ensure that you do so in a
way that won't be rewritten. Ideally as part of your Keystone packaging, or
better yet disable v2 if you can to avoid this whole mess. You do not want this
being reverted since if this code isn't there MFA is entirely useless and can
easily be bypassed by v2 authentication.**
