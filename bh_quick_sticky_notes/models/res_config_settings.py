# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quick_sticky_note_model_ids = fields.Many2many(
        'ir.model',
        'res_config_settings_quick_sticky_note_rel',
        'config_id',
        'model_id',
        string='Models with Sticky Notes',
        domain="[('transient', '=', False)]",
        help='Select the models where the Quick Sticky Notes panel should appear on form views.',
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        enabled = self.env['quick.sticky.note.model'].sudo().search([])
        res.update({
            'quick_sticky_note_model_ids': [(6, 0, enabled.mapped('model_id').ids)],
        })
        return res

    def set_values(self):
        super().set_values()
        Enabled = self.env['quick.sticky.note.model'].sudo()
        current = Enabled.search([])
        selected_model_ids = set(self.quick_sticky_note_model_ids.ids)
        current_model_ids = set(current.mapped('model_id').ids)

        to_remove = current.filtered(lambda r: r.model_id.id not in selected_model_ids)
        to_remove.unlink()

        for model_id in selected_model_ids - current_model_ids:
            Enabled.create({'model_id': model_id})
