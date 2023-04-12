# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from datetime import date, datetime, timedelta

from odoo.tests.common import Form, TransactionCase


class TestOrderpointNoHorizon(TransactionCase):
    def setUp(self):
        super(TestOrderpointNoHorizon, self).setUp()
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.product = self.env["product.product"].create(
            {"name": "Test Orderpoint No Horizon", "type": "product"}
        )

    def test_reordering_rule_no_horizon(self):
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        orderpoint_form = Form(self.env["stock.warehouse.orderpoint"])
        orderpoint_form.product_id = self.product
        orderpoint_form.location_id = warehouse.lot_stock_id
        orderpoint_form.product_min_qty = 0.0
        orderpoint_form.product_max_qty = 5.0
        orderpoint = orderpoint_form.save()

        # get auto-created pull rule from when warehouse is created
        rule = self.env["stock.rule"].search(
            [
                ("route_id", "=", warehouse.reception_route_id.id),
                ("location_id", "=", warehouse.lot_stock_id.id),
                (
                    "location_src_id",
                    "=",
                    self.env.ref("stock.stock_location_suppliers").id,
                ),
                ("action", "=", "pull"),
                ("procure_method", "=", "make_to_stock"),
                ("picking_type_id", "=", warehouse.in_type_id.id),
            ]
        )

        # add a delay [i.e. lead days] so procurement will be triggered based on forecasted stock
        rule.delay = 9.0

        delivery_move = self.env["stock.move"].create(
            {
                "name": "Delivery",
                "date": datetime.today() + timedelta(days=5),
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 12.0,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": self.ref("stock.stock_location_customers"),
            }
        )
        delivery_move._action_confirm()
        orderpoint._compute_qty()
        self.env["procurement.group"].run_scheduler()

        receipt_move = self.env["stock.move"].search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", self.env.ref("stock.stock_location_suppliers").id),
            ]
        )
        self.assertTrue(receipt_move)
        self.assertEqual(receipt_move.date.date(), date.today())
        self.assertEqual(receipt_move.product_uom_qty, 17.0)
        self.assertEqual(orderpoint.qty_forecast, orderpoint.product_max_qty)

        # Postpone the reception
        receipt_move.date += timedelta(days=20)
        orderpoint.invalidate_cache(["qty_forecast"])
        # Check this has no impact no the forecasted quantity
        self.assertEqual(orderpoint.qty_forecast, orderpoint.product_max_qty)
