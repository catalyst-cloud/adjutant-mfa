Adjutant MFA
================

This repo contains all code necessary to implement TOTP MFA in an OpenStack
cloud using Keystone plugins and the Adjutant framework.

The README in each sub-folder will help you get started with each element, but
all three are needed to make this MFA method work in a useful user friendly
fashion.


Keystone Plugin
----------------

The Keystone plugin can be installed in place of the password auth method.

It will act like the password auth method until a user has an additional
credential added with the type 'totp'. This credential is the key for
totp generation. Credential access is typically restricted to admin users so
the Adjutant task provides a way for users to manage their own TOTP credentials.

The MFA passcode is submitted by appending to the end of the users password.

This plugin will only work with v3 Keystone, so deployers either need to disable
v2 or add some additional code to the v2 auth logic to block MFA enabled users
from using v2.


Adjutant Task and Action
------------------------

The additional Adjutant task and action contained inside the plugin. This
exposes an API allow users to request to add a MFA or remove MFA from their
account. A random TOTP key is generated and the user must submit a valid TOTP
passcode to confirm the addition or removal of MFA from their account.

There is also an alternative UserList view that augments the existing Adjutant
user list with a value that shows if a user has MFA enabled which is useful for
project admins to be able to audit.


Horizon Plugin
------------------------

The horizon plugin introduces a new panel in the settings dashboard, which
provides a nice interface to the Adjutant API for adding or removing MFA
credentials.

It also has some overrides for Horizon that add some additional MFA specific
features to Horizon, and the existing Adjutant panels.
