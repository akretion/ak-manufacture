# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import fields, models, api
from openerp.osv import fields as old_fields


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'

    def _is_pending(self, cr, uid, ids, field, args, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = False
            for depend_line in line.dependency_ids:
                if depend_line.state != 'done':
                    result[line.id] = True
                    break
        for line_id, val in result.items():
            self.write(cr, uid, line_id, {
                'pending': val,
                }, context=context)
        return result

    def _get_operation_from_dependency(self, cr, uid, ids, context=None):
        res = []
        if context is None:
            context = {}
        elif context.get('create_line'):
            res = ids[:]
        for line in self.read(cr, uid, ids, ['dependency_for_ids'],
                              context=context):
            res.extend(line['dependency_for_ids'])
        return res

    def _get_operation_rom_routing_line(self, cr, uid, ids, context=None):
        res = self.pool['mrp.production.workcenter.line'].search(cr, uid,
            [('routing_line_id', 'in', ids),
             ('state', 'not in', ('cancel', 'done'))])
        print len(res)
        return res

    # Keep pending in old api for now else it won't recompute, because
    # dependency_ids is not stored. I am not sure it is a good idea to
    # Store it.
    _columns = {
        'pending': old_fields.function(
            _is_pending,
            type='boolean',
            string='Pending',
            select=True,
            store={
                'mrp.production.workcenter.line': [
                    _get_operation_from_dependency,
                    ['state', 'routing_line_id'],
                    10,
                ],
                'mrp.routing.workcenter': [
                    _get_operation_rom_routing_line,
                    ['dependency_ids'],
                    10,
                ],
            },
        ),
    }

    @api.multi
    def _get_dependency_ids(self):
        for line in self:
            if line.routing_line_id.dependency_ids:
                routing_line_ids = line.routing_line_id.dependency_ids.ids
                depend_lines = self.search([
                    ['production_id', '=', line.production_id.id],
                    ['routing_line_id', 'in', routing_line_ids],
                    ])
                line.dependency_ids = [(6 ,0, depend_lines.ids)] 

    @api.multi
    def _get_dependency_for_ids(self):
        for line in self:
            if line.routing_line_id.dependency_for_ids:
                routing_line_ids = line.routing_line_id.dependency_for_ids.ids
                depend_lines = self.search([
                    ['production_id', '=', line.production_id.id],
                    ['routing_line_id', 'in', routing_line_ids],
                    ])
                line.dependency_for_ids = [(6 ,0, depend_lines.ids)]

#    @api.multi
#    @api.depends('dependency_ids.state', 'dependency_ids.routing_line_id')
#    def _is_pending(self):
#        print 'll', self
#        for line in self:
#            result[line.id] = False
#            for depend_line in line.dependency_ids:
#                if depend_line.state != 'done':
#                    line.pending = True
#                    break


#    pending = fields.Boolean(
#        '_is_pending',
#        store=True)

    routing_line_id = fields.Many2one(
        'mrp.routing.workcenter',
        'Routing Line')

    dependency_ids = fields.Many2many(
        compute='_get_dependency_ids',
        comodel_name='mrp.production.workcenter.line',
        string='Dependency')
    dependency_for_ids = fields.Many2many(
        compute='_get_dependency_for_ids',
        comodel_name='mrp.production.workcenter.line',
        string='Dependency for')

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['create_line'] = True
        return super(MrpProductionWorkcenterLine, self).create(
            cr, uid, vals, context=ctx)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'


    @api.model
    def _prepare_wc_line(self, bom, wc_use, level=0, factor=1):
        res = super(MrpBom, self)._prepare_wc_line(
            bom, wc_use, factor=factor, level=level)
        res['routing_line_id'] = wc_use.id
        return res


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    dependency_ids = fields.Many2many(
            'mrp.routing.workcenter',
            'rel_dependency_routing_worcenter',
            'routing_id',
            'routing_dependency_id',
            'Depend On')
    dependency_for_ids = fields.Many2many(
            'mrp.routing.workcenter',
            'rel_dependency_routing_worcenter',
            'routing_dependency_id',
            'routing_id',
            'Dependency For')
