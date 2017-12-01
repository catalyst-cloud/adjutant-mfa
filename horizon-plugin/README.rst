===============================
Adjutant MFA User interface
===============================

Horizon plugin for Adjutant MFA plugin.

Installation Instructions:
----------------------------

The main Adjutant UI plugin must first be installed with at least the
adjutant_base enabled file in use.

Please see https://github.com/catalyst/adjutant-ui for instructions.

To install this plugin install the python libray to Horizon's virtual environment
and copy over the enabled files in adjutant_mfa_ui/enabled.

The new panel will be placed in the setting dashboard and there will be an
additional option on the main login page for users to place their TOTP passcode
in.
