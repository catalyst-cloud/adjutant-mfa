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

If you would like the edited OpenRC file to be available on the API Access
page add this line into your ``local_settings.py``.

.. code-block:: python

    HORIZON_CONFIG["customization_module"] = "adjutant_mfa_ui.overrides"

If you would like the edited OpenRC file available on the user menu add this
line into your ``local_settings.py``.

.. code-block:: python

  HORIZON_CONFIG['user_menu_links'].append({
    'name': 'OpenStack RC File v3 (MFA Enabled)',
    'url': 'horizon:settings:mfa:openrc'})
