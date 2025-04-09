# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo.addons.queue_job.tests.common import trap_jobs
from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestAssignAutoRelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "no_backorder_at_release": True,
            }
        )
        cls.in_type = cls.wh.in_type_id
        cls.loc_supplier = cls.env.ref("stock.stock_location_suppliers")
        cls.shipping = cls._out_picking(
            cls._create_picking_chain(
                cls.wh, [(cls.product1, 10)], date=datetime(2019, 9, 2, 16, 0)
            )
        )
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 5.0)
        cls.shipping.release_available_to_promise()
        cls.picking = cls._prev_picking(cls.shipping)
        cls.picking.action_assign()
        cls.unreleased_move = cls.shipping.move_ids.filtered("need_release")

    def _create_move(
        self,
        product,
        picking_type,
        qty=1.0,
        state="confirmed",
        procure_method="make_to_stock",
        move_dest=None,
    ):
        source = picking_type.default_location_src_id or self.loc_supplier
        dest = picking_type.default_location_dest_id or self.loc_customer
        move_vals = {
            "name": product.name,
            "product_id": product.id,
            "product_uom_qty": qty,
            "product_uom": product.uom_id.id,
            "picking_type_id": picking_type.id,
            "location_id": source.id,
            "location_dest_id": dest.id,
            "state": state,
            "procure_method": procure_method,
        }
        if move_dest:
            move_vals["move_dest_ids"] = [(4, move_dest.id, False)]
        return self.env["stock.move"].create(move_vals)

    def _receive_product(self, product=None, qty=None):
        qty = qty or 100
        move = self._create_move(product or self.product1, self.in_type, qty=qty)
        move._action_assign()
        move.move_line_ids.qty_done = qty
        move.move_line_ids.location_dest_id = self.loc_bin1.id
        move._action_done()

    def _get_job_for_method(self, jobs, method):
        for job in jobs:
            if str(job.func) == str(method):
                return job
        return None

    def test_product_pickings_auto_release_exclude_location(self):
        """
        Test the behavior of auto-releasing pickings when a location is excluded
        from immediately usable quantities."""
        self.assertEqual(1, len(self.unreleased_move))
        self.assertEqual(1, len(self.picking.move_ids))
        self.assertEqual(5, self.picking.move_ids.product_qty)
        self.loc_bin1.exclude_from_immediately_usable_qty = True
        with trap_jobs() as trap:
            self._receive_product(self.product1, 100)
            self.product1.pickings_auto_release()
            job = self._get_job_for_method(
                trap.enqueued_jobs,
                self.unreleased_move.picking_id.auto_release_available_to_promise,
            )
            self.assertFalse(job)
        self.assertTrue(self.unreleased_move.need_release)
