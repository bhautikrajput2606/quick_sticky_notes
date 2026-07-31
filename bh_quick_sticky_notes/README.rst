=================
Quick Sticky Notes
=================

**Odoo 19** free app: sticky notes on any enabled record form.

Features
--------

* Enable sticky notes per model from **Settings → General Settings → Quick Sticky Notes**
* Sticky panel on the form (not on login, not replacing Chatter)
* Multiple notes, colors, pin, private/shared visibility
* Author + timestamps
* **My Notes** / **All Notes** menus
* Access rules so private notes stay private

Installation
------------

1. Copy ``bh_quick_sticky_notes`` into your Odoo addons path.
2. Update the Apps list and install **Quick Sticky Notes**.
3. Open **Settings → General Settings → Quick Sticky Notes** and enable models
   (Contacts / ``res.partner`` is enabled by default).
4. Open an enabled record form and use the sticky notes panel.

Technical notes
---------------

* Depends only on ``base``, ``base_setup``, and ``web``.
* Injects an OWL panel into ``web.FormView`` (no auth/login customization).
* License: LGPL-3

Tests
-----

Run::

    odoo-bin -d YOUR_DB -i bh_quick_sticky_notes --test-enable --stop-after-init
