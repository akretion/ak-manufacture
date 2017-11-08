# -*- coding: utf-8 -*-
##############################################################################
#
#  license AGPL version 3 or later
#  see license in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2015 Akretion (http://www.akretion.com).
#  @author Florian da Costa <florian.dacosta@akretion.com>
#
##############################################################################

from openerp import models, api


class OrderWorkorder(models.TransientModel):
    _name = 'order.workorder'

    @api.multi
    def order_workorders(self):
        MrpWorkcenter = self.env['mrp.workcenter']
        active_ids = self.env.context.get('active_ids', [])
        workcenters = MrpWorkcenter.browse(active_ids)
        workcenters.button_order_workorder()
        return True
