# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    orderpoint_calendar_id = fields.Many2one(
        related="company_id.orderpoint_calendar_id",
        readonly=False,
    )
    orderpoint_on_workday = fields.Boolean(
        related="company_id.orderpoint_on_workday",
        readonly=False,
    )
