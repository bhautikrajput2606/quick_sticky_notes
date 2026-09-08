# -*- coding: utf-8 -*-
{
    'name': 'Quick Sticky Notes',
    'version': '18.0.1.0.1',
    'category': 'Productivity',
    'summary': 'Sticky notes on any Odoo record — private or shared, colorful and pinned',
    'description': """
Quick Sticky Notes
==================

Add Chatter-style sticky notes on any enabled record form.

Features
--------
* Enable sticky notes on selected models from Settings
* Colorful sticky panel on the form view
* Multiple notes per record with pin, private/shared visibility
* Author and date tracking
* My Notes menu for a global overview
* Secure record rules for private notes

Designed for Odoo 18 and the Odoo Apps Store (free / LGPL-3).
    """,
    'author': 'Bhautik Rajput',
    'website': 'https://apps.odoo.com/apps/modules/19.0/bh_quick_sticky_notes/',
    'license': 'OPL-1',
    'price': 9.99,
    'currency': 'USD',
    'depends': [
        'base',
        'base_setup',
        'web',
    ],
    'data': [
        'security/quick_sticky_note_security.xml',
        'security/ir.model.access.csv',
        'views/quick_sticky_note_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bh_quick_sticky_notes/static/src/components/sticky_notes_panel/sticky_notes_panel.scss',
            'bh_quick_sticky_notes/static/src/components/sticky_notes_panel/sticky_notes_panel.xml',
            'bh_quick_sticky_notes/static/src/components/sticky_notes_panel/sticky_notes_panel.js',
            'bh_quick_sticky_notes/static/src/js/form_view_patch.js',
            'bh_quick_sticky_notes/static/src/js/form_view_patch.xml',
        ],
    },
    'images': [
        'static/description/banner_screenshot.png',
        'static/description/main_screenshot.png',
        'static/description/screenshot_colors.png',
        'static/description/screenshot_settings.png',
        'static/description/screenshot_mynotes.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
