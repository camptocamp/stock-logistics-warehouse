# Copyright 2019 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class VerticalLiftOperationTransfer(models.AbstractModel):
    _inherit = "vertical.lift.operation.transfer"

    product_qty_by_packaging_display = fields.Char(
        related="current_move_line_id.product_qty_by_packaging_display"
    )
