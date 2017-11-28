Adjutant MFA
================

This repo contains all code necessary to implement TOTP MFA in an openstack
cloud using Keystone and the Adjutant framework.


Keystone Plugin
----------------

The keystone plugin can be installed in place of the password auth method.

It will act like the password auth method until a user has an additional
credential added with the type 'totp'. This credential is the key for
totp generation. Credential access is typically restricted to admin users so
the Adjutant task provides a way for users to manage their own TOTP credentials.

The MFA passcode is submitted by appending to the end of the users password.

This plugin will only work with v3 keystone, and will force users with TOTP
credentials setup to use v3.


Adjutant Task and Action
------------------------

The additional Adjutant task and action contained inside the plugin. This
exposes an API allow users to request to add a MFA or remove MFA from their
account. A random TOTP key is generated and the user must submit a valid TOTP
passcode to confirm the addition or removal of MFA from their account.


Horizon Plugin
------------------------

The horizon plugin introduces a new panel in the settings dashboard, which
provides a nice interface to the Adjutant API for adding or removing MFA
credentials.
