# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Enable sticky notes on Contacts by default."""
    partner_model = env['ir.model'].sudo().search([('model', '=', 'res.partner')], limit=1)
    if partner_model and not env['quick.sticky.note.model'].sudo().search_count([
        ('model_id', '=', partner_model.id),
    ]):
        env['quick.sticky.note.model'].sudo().create({
            'model_id': partner_model.id,
        })
