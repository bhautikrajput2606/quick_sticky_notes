# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class QuickStickyNoteModel(models.Model):
    _name = 'quick.sticky.note.model'
    _description = 'Enabled Model for Quick Sticky Notes'
    _order = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        domain="[('transient', '=', False)]",
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Technical Name',
        store=True,
        readonly=True,
        index=True,
    )
    name = fields.Char(related='model_id.name', string='Model Name', readonly=True)

    _model_id_uniq = models.Constraint(
        'unique(model_id)',
        'This model is already enabled for sticky notes.',
    )

    @api.constrains('model_id')
    def _check_model_not_self(self):
        blocked = {
            'quick.sticky.note',
            'quick.sticky.note.model',
        }
        for rec in self:
            if rec.model_name in blocked:
                raise ValidationError(
                    self.env._('Sticky notes cannot be enabled on Quick Sticky Notes models.')
                )

    @api.model
    def is_model_enabled(self, model_name):
        if not model_name:
            return False
        return bool(self.sudo().search_count([('model_name', '=', model_name)], limit=1))

    @api.model
    def get_enabled_model_names(self):
        return self.sudo().search([]).mapped('model_name')
