# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class QuickStickyNote(models.Model):
    _name = 'quick.sticky.note'
    _description = 'Quick Sticky Note'
    _order = 'is_pinned desc, write_date desc, id desc'

    COLORS = [
        ('yellow', 'Yellow'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('orange', 'Orange'),
        ('pink', 'Pink'),
    ]

    name = fields.Char(string='Title')
    body = fields.Text(string='Note', required=True)
    color = fields.Selection(COLORS, string='Color', default='yellow', required=True)
    is_pinned = fields.Boolean(string='Pinned', default=False)
    visibility = fields.Selection(
        [
            ('private', 'Private'),
            ('shared', 'Shared'),
        ],
        string='Visibility',
        default='private',
        required=True,
        help='Private notes are visible only to the author. '
             'Shared notes are visible to internal users who can access the record.',
    )
    res_model = fields.Char(string='Related Model', required=True, index=True)
    res_id = fields.Integer(
        string='Related Record ID',
        required=True,
        index=True,
    )
    res_name = fields.Char(
        string='Related Record',
        compute='_compute_res_name',
        store=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Author',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True,
    )
    @api.depends('name', 'body', 'res_name')
    def _compute_display_name(self):
        for note in self:
            title = (note.name or '').strip()
            if not title:
                title = (note.body or '')[:40]
                if note.body and len(note.body) > 40:
                    title = '%s…' % title
            if note.res_name:
                note.display_name = '%s (%s)' % (title, note.res_name)
            else:
                note.display_name = title or self.env._('Sticky Note')

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for note in self:
            note.res_name = note._get_related_record_display()

    def _get_related_record_display(self):
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return False
        if self.res_model not in self.env:
            return False
        try:
            record = self.env[self.res_model].browse(self.res_id).exists()
            if not record:
                return False
            if not record.has_access('read'):
                return self.env._('Restricted record')
            return record.display_name
        except Exception:
            return False

    def _check_enabled_model(self, res_model):
        if not self.env['quick.sticky.note.model'].is_model_enabled(res_model):
            raise UserError(
                self.env._(
                    'Sticky notes are not enabled for model "%(model)s". '
                    'Enable it under Settings → General Settings → Quick Sticky Notes.',
                    model=res_model,
                )
            )

    def _check_related_record_access(self, res_model, res_id, mode='read'):
        if not res_model or not res_id:
            raise ValidationError(self.env._('A related record is required.'))
        if res_model not in self.env:
            raise ValidationError(self.env._('Unknown model: %s', res_model))
        record = self.env[res_model].browse(res_id)
        if not record.exists():
            raise ValidationError(self.env._('The related record no longer exists.'))
        try:
            record.check_access(mode)
        except AccessError as err:
            raise AccessError(
                self.env._(
                    'You do not have access to the related record for this sticky note.'
                )
            ) from err
        return record

    def _prepare_company(self, res_model, res_id):
        record = self.env[res_model].browse(res_id)
        if 'company_id' in record._fields and record.company_id:
            return record.company_id.id
        return self.env.company.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            res_model = vals.get('res_model')
            res_id = vals.get('res_id')
            self._check_enabled_model(res_model)
            self._check_related_record_access(res_model, res_id, mode='read')
            vals.setdefault('user_id', self.env.user.id)
            if not vals.get('company_id'):
                vals['company_id'] = self._prepare_company(res_model, res_id)
            if not (vals.get('body') or '').strip():
                raise ValidationError(self.env._('Note content cannot be empty.'))
        return super().create(vals_list)

    def _can_manage_note(self, note):
        return (
            self.env.su
            or note.user_id == self.env.user
            or self.env.user.has_group('base.group_system')
        )

    def write(self, vals):
        if 'body' in vals and not (vals.get('body') or '').strip():
            raise ValidationError(self.env._('Note content cannot be empty.'))
        for note in self:
            if not self._can_manage_note(note):
                raise AccessError(self.env._('Only the author can edit this sticky note.'))
            res_model = vals.get('res_model', note.res_model)
            res_id = vals.get('res_id', note.res_id)
            if 'res_model' in vals or 'res_id' in vals:
                self._check_enabled_model(res_model)
                self._check_related_record_access(res_model, res_id, mode='read')
        return super().write(vals)

    def unlink(self):
        for note in self:
            if not self._can_manage_note(note):
                raise AccessError(self.env._('Only the author can delete this sticky note.'))
        return super().unlink()

    def action_open_related_record(self):
        self.ensure_one()
        self._check_related_record_access(self.res_model, self.res_id, mode='read')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_panel_data(self, res_model, res_id):
        """Return sticky panel payload for the OWL form widget."""
        enabled = self.env['quick.sticky.note.model'].is_model_enabled(res_model)
        if not enabled or not res_id:
            return {
                'enabled': False,
                'notes': [],
                'colors': self.COLORS,
            }
        try:
            self._check_related_record_access(res_model, res_id, mode='read')
        except (AccessError, ValidationError):
            return {
                'enabled': False,
                'notes': [],
                'colors': self.COLORS,
            }

        notes = self.search([
            ('res_model', '=', res_model),
            ('res_id', '=', res_id),
        ])
        return {
            'enabled': True,
            'notes': notes._panel_note_dicts(),
            'colors': self.COLORS,
            'current_user_id': self.env.user.id,
        }

    def _panel_note_dicts(self):
        result = []
        for note in self:
            result.append({
                'id': note.id,
                'name': note.name or '',
                'body': note.body or '',
                'color': note.color,
                'is_pinned': note.is_pinned,
                'visibility': note.visibility,
                'user_id': note.user_id.id,
                'user_name': note.user_id.name,
                'create_date': fields.Datetime.to_string(note.create_date),
                'write_date': fields.Datetime.to_string(note.write_date),
                'is_author': note.user_id == self.env.user,
            })
        return result

    @api.model
    def create_from_panel(self, values):
        vals = {
            'name': (values.get('name') or '').strip() or False,
            'body': (values.get('body') or '').strip(),
            'color': values.get('color') or 'yellow',
            'is_pinned': bool(values.get('is_pinned')),
            'visibility': values.get('visibility') or 'private',
            'res_model': values.get('res_model'),
            'res_id': values.get('res_id'),
        }
        note = self.create(vals)
        return note._panel_note_dicts()[0]

    def update_from_panel(self, values):
        self.ensure_one()
        vals = {}
        for key in ('name', 'body', 'color', 'is_pinned', 'visibility'):
            if key in values:
                vals[key] = values[key]
        if 'name' in vals:
            vals['name'] = (vals['name'] or '').strip() or False
        if 'body' in vals:
            vals['body'] = (vals['body'] or '').strip()
        self.write(vals)
        return self._panel_note_dicts()[0]

    def delete_from_panel(self):
        self.ensure_one()
        self.unlink()
        return True
