===============================
Keystone MFA Plugin
===============================

This adds an authenetication plugin to Keystone such that if the user
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
includes checkes to prevent users from adding a credenial they do not have
stored in a generator.

The password-totp plugin requires keystone V3, it will block people from
using V2, if they have TOTP credentials on them.

Works as normal password plugin if no TOTP credentials present for user,
otherwise expects totp passcode appended to the password.


Installing in Devstack
------------------------

The current code provided works for Mitaka keystone, but should work with
only a few modifications for later versions of keystone.

Files should be dropped in as replacements for the same name files in keystone.

In the auth section of the keystone.conf file add:

.. code-block::
  password = keystone.auth.plugins.password_totp.PasswordTOTP

Then restart the keystone server.
