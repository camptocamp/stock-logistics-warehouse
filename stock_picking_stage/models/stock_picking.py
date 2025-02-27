# Copyright 2025 Camptocamp SA
# @author: Italo LOPES <italo.lopes@camptocamp.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    picking_stage_id = fields.Many2one("stock.picking.stage", index=True, tracking=True)
    picking_stage_code = fields.Char(related="picking_stage_id.code")
    picking_stage_color = fields.Integer(related="picking_stage_id.color")
