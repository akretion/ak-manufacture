# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: David BEAL
#    Copyright 2015 Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.addons.mrp_workcenter_workorder_link.models.mrp import (
    STATIC_STATES
)
from openerp.addons.base.ir.ir_model import _get_fields_type


COMPLEX_WORK_ORDER_FIELDS = [
    'message_follower_ids',
    'message_is_follower',
    'message_unread',
]


class MrpWorkcenterOrderingKey(models.Model):
    _name = 'mrp.workcenter.ordering.key'
    _description = "Workcenter Ordering Key"

    name = fields.Char('Name')
    field_ids = fields.One2many(
        'mrp.workcenter.ordering.field',
        'ordering_key_id',
        'Fields')


class MrpWorkcenterOrderingField(models.Model):
    _name = 'mrp.workcenter.ordering.field'
    _description = "Workcenter Ordering Field"
    _order = 'sequence ASC'

    sequence = fields.Integer(
        'Sequence')
    ordering_key_id = fields.Many2one(
        'mrp.workcenter.ordering.key',
        'Workcenter')
    field_id = fields.Many2one(
        'ir.model.fields',
        string='Work Order Field',
        domain=[('model', '=', 'mrp.production.workcenter.line'),
                ('name', 'not in', COMPLEX_WORK_ORDER_FIELDS)])
    ttype = fields.Selection(
        '_get_fields_type',
        related='field_id.ttype',
        string='Type',
        readonly=True)
    order = fields.Selection(
        [('asc', 'Asc'), ('desc', 'Desc')],
        string='Order',
        default='asc')


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    priority = fields.Integer('Priority')


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'
    _order = 'sequence'

    @api.multi
    def _get_operation_from_routing(self):
        return self.env['mrp.production.workcenter.line'].search([
            ['routing_line_id', '=', self.ids],
            ])

    priority = fields.Integer(
        related='routing_line_id.priority',
        store=True
    )


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    workcenter_line_ids = fields.One2many(
        'mrp.routing.workcenter',
        'workcenter_id',
        'Work Centers')
    waiting_load = fields.Float('Waiting (h)')
    todo_load = fields.Float('Todo (h)')
    scheduled_load = fields.Float('Scheduled (h)')
    ordering_key_id = fields.Many2one(
        'mrp.workcenter.ordering.key',
        string='Ordering Key',
        help="Allow to define Work Orders ordering priority")

    @api.multi
    def _get_sql_load_select(self):
        select = super(MrpWorkcenter, self)._get_sql_load_select()
        select.append('mp.schedule_state')
        return select

    @api.multi
    def _get_sql_load_group(self):
        group = super(MrpWorkcenter, self)._get_sql_load_group()
        group.append('mp.schedule_state')
        return group

    api.multi
    def _set_load_in_vals(self, data, elm):
        super(MrpWorkcenter, self)._set_load_in_vals(data, elm)
        field = '%s_load' % elm['schedule_state']
        data[elm['workcenter']][field] += elm['hour']

    api.model
    def _get_default_workcenter_vals(self):
        default = super(MrpWorkcenter, self)._get_default_workcenter_vals()
        for col in self._columns:
            if len(col) > 3 and col[-4:] == 'load':
                default.update({col: 0})
        return default

    @api.multi
    def button_order_workorder(self):
        workorder_obj = self.env['mrp.production.workcenter.line']
        for workcenter in self:
            if not workcenter.ordering_key_id:
                raise UserError(
                    _('The automatic ordering can not be processed as the '
                      'ordering key is empty. Please go in the tab "Ordering"'
                      ' and fill the field "ordering key"'))
            order_by = ['%s %s' % (row.field_id.name, row.order)
                        for row in workcenter.ordering_key_id.field_ids]
            prod_lines = workorder_obj.search([
                ('state', 'not in', STATIC_STATES),
                ('workcenter_id', '=', workcenter.id),
                ], order=', '.join(order_by))
            count = 1
            for prod_line in prod_lines:
                vals = {'sequence': count}
                count += 1
                prod_line.write(vals)
        return True
