# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

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

    def test_product_pickings_auto_release_exclude_location(self):
        """
        Test the behavior of auto-releasing pickings when a location is excluded
        from immediately usable quantities."""
        self.assertEqual(1, len(self.unreleased_move))
        self.assertEqual(1, len(self.picking.move_ids))
        self.assertEqual(5, self.picking.move_ids.product_qty)
        self.loc_bin1.exclude_from_immediately_usable_qty = True
        self._update_qty_in_location(self.loc_bin1, self.product1, 100)
        self.assertTrue(self.unreleased_move.need_release)
