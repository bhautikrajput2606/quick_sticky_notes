# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestQuickStickyNote(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Note = cls.env['quick.sticky.note']
        cls.Enabled = cls.env['quick.sticky.note.model']
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        cls.user_model = cls.env['ir.model'].search([('model', '=', 'res.users')], limit=1)

        cls.Enabled.search([]).unlink()
        cls.Enabled.create({'model_id': cls.partner_model.id})

        cls.partner = cls.env['res.partner'].create({'name': 'Sticky Notes Partner'})
        cls.partner_other = cls.env['res.partner'].create({'name': 'Other Partner'})

        cls.user_a = cls.env['res.users'].create({
            'name': 'Sticky User A',
            'login': 'sticky_user_a',
            'email': 'sticky_a@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'Sticky User B',
            'login': 'sticky_user_b',
            'email': 'sticky_b@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_01_create_private_note(self):
        note = self.Note.with_user(self.user_a).create({
            'body': 'Private follow-up',
            'visibility': 'private',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
            'color': 'yellow',
        })
        self.assertEqual(note.user_id, self.user_a)
        self.assertTrue(note.display_name)

        with self.assertRaises(AccessError):
            note.with_user(self.user_b).read(['body'])

    def test_02_shared_note_visible_to_others(self):
        note = self.Note.with_user(self.user_a).create({
            'body': 'Shared reminder',
            'visibility': 'shared',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
        })
        self.assertEqual(
            note.with_user(self.user_b).body,
            'Shared reminder',
        )
        with self.assertRaises(AccessError):
            note.with_user(self.user_b).write({'body': 'Hacked'})

    def test_03_disabled_model_rejected(self):
        with self.assertRaises(UserError):
            self.Note.with_user(self.user_a).create({
                'body': 'Should fail',
                'res_model': 'res.users',
                'res_id': self.user_a.id,
            })

    def test_04_empty_body_rejected(self):
        with self.assertRaises(ValidationError):
            self.Note.with_user(self.user_a).create({
                'body': '   ',
                'res_model': 'res.partner',
                'res_id': self.partner.id,
            })

    def test_05_panel_data_and_crud(self):
        panel = self.Note.with_user(self.user_a).get_panel_data('res.partner', self.partner.id)
        self.assertTrue(panel['enabled'])
        self.assertEqual(panel['notes'], [])

        created = self.Note.with_user(self.user_a).create_from_panel({
            'name': 'Call back',
            'body': 'Tomorrow morning',
            'color': 'green',
            'is_pinned': True,
            'visibility': 'private',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
        })
        self.assertTrue(created['id'])
        self.assertTrue(created['is_pinned'])
        self.assertTrue(created['is_author'])

        updated = self.Note.with_user(self.user_a).browse(created['id']).update_from_panel({
            'body': 'Updated text',
            'color': 'blue',
        })
        self.assertEqual(updated['body'], 'Updated text')
        self.assertEqual(updated['color'], 'blue')

        panel = self.Note.with_user(self.user_a).get_panel_data('res.partner', self.partner.id)
        self.assertEqual(len(panel['notes']), 1)

        self.Note.with_user(self.user_a).browse(created['id']).delete_from_panel()
        panel = self.Note.with_user(self.user_a).get_panel_data('res.partner', self.partner.id)
        self.assertEqual(panel['notes'], [])

    def test_06_settings_sync_enabled_models(self):
        settings = self.env['res.config.settings'].create({})
        settings.quick_sticky_note_model_ids = [(6, 0, [self.partner_model.id, self.user_model.id])]
        settings.set_values()
        enabled_names = set(self.Enabled.get_enabled_model_names())
        self.assertIn('res.partner', enabled_names)
        self.assertIn('res.users', enabled_names)

        settings.quick_sticky_note_model_ids = [(6, 0, [self.partner_model.id])]
        settings.set_values()
        enabled_names = set(self.Enabled.get_enabled_model_names())
        self.assertEqual(enabled_names, {'res.partner'})

    def test_07_panel_hidden_when_model_not_enabled(self):
        panel = self.Note.with_user(self.user_a).get_panel_data('res.users', self.user_a.id)
        self.assertFalse(panel['enabled'])

    def test_08_author_only_unlink(self):
        note = self.Note.with_user(self.user_a).create({
            'body': 'Do not delete',
            'visibility': 'shared',
            'res_model': 'res.partner',
            'res_id': self.partner.id,
        })
        with self.assertRaises(AccessError):
            note.with_user(self.user_b).unlink()
