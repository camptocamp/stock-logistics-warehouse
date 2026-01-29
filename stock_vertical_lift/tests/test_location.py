# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tools import mute_logger

from .common import VerticalLiftCase

SHUTTLE_LOGGER = "odoo.addons.stock_vertical_lift.models.vertical_lift_shuttle"


class TestVerticalLiftLocation(VerticalLiftCase):
    def test_vertical_lift_kind(self):
        # this boolean is what defines a "Vertical Lift View", the upper level
        # of the tree (View -> Shuttles -> Trays -> Cells)
        self.assertTrue(self.vertical_lift_loc.vertical_lift_location)
        self.assertEqual(self.vertical_lift_loc.vertical_lift_kind, "view")

        # check types accross the hierarchy
        shuttles = self.vertical_lift_loc.child_ids
        self.assertTrue(
            all(location.vertical_lift_kind == "shuttle" for location in shuttles)
        )
        trays = shuttles.mapped("child_ids")
        self.assertTrue(
            all(location.vertical_lift_kind == "tray" for location in trays)
        )
        cells = trays.mapped("child_ids")
        self.assertTrue(
            all(location.vertical_lift_kind == "cell" for location in cells)
        )

    @mute_logger(SHUTTLE_LOGGER)
    def test_fetch_vertical_lift_tray(self):
        shuttles = self.vertical_lift_loc.child_ids
        trays = shuttles.mapped("child_ids")
        cells = trays.mapped("child_ids")
        # FIXME:
        # odoo.exceptions.MissingError: Record does not exist or has been deleted.
        # (Record: vertical.lift.shuttle(<id>), User: 1)
        self.assertTrue(
            cells[0]
            .with_context(shuttle_id=shuttles[0].id)
            .button_fetch_vertical_lift_tray()
        )
        message = "cell_location cannot be set when the location is a cell."
        with self.assertRaisesRegex(ValueError, message):
            cells[0].fetch_vertical_lift_tray(cells[0], shuttle=shuttles[0])
        message = "Cannot fetch a vertical lift tray on location"
        with self.assertRaisesRegex(exceptions.UserError, message):
            shuttles[0].fetch_vertical_lift_tray(cells[0])
        self.assertTrue(cells[0].button_release_vertical_lift_tray())

    def test_create_shuttle(self):
        # any location created directly under the view is a shuttle
        shuttle_loc = self.env["stock.location"].create(
            {
                "name": "Shuttle 42",
                "location_id": self.vertical_lift_loc.id,
                "usage": "internal",
            }
        )
        self.assertEqual(shuttle_loc.vertical_lift_kind, "shuttle")

    def test_shared_storage_location_kind(self):
        """Test that shared storage locations correctly identify as 'shuttle' kind."""
        # 1. Create a standard location anywhere in the warehouse
        # (Not under the vertical_lift_loc view)
        shared_loc = self.env["stock.location"].create(
            {
                "name": "External Shared Zone",
                "location_id": self.stock_location.id,
                "usage": "internal",
            }
        )
        # Initially, it should not have a lift kind
        self.assertFalse(shared_loc.vertical_lift_kind)

        # 2. Link this location as shared storage for our shuttle
        # This should trigger the recompute via inverse_vertical_lift_shuttle_ids
        self.shuttle.write(
            {
                "use_shared_storage_location": True,
                "shared_storage_location_id": shared_loc.id,
            }
        )

        # 3. Verify it is now a 'shuttle' kind
        self.assertEqual(
            shared_loc.vertical_lift_kind,
            "shuttle",
            "Location should become 'shuttle' kind when linked as shared storage",
        )

        # 4. Verify the hierarchy still works (trays/cells under the shared location)
        shared_tray = self.env["stock.location"].create(
            {
                "name": "Shared Tray 1",
                "location_id": shared_loc.id,
                "usage": "internal",
            }
        )
        self.assertEqual(
            shared_tray.vertical_lift_kind,
            "tray",
            "Child of a shared storage location should be identified as a tray",
        )

        # 5. Verify reversion: unlinking it should remove the 'shuttle' kind
        self.shuttle.use_shared_storage_location = False
        # shared_storage_location_id will now sync to shuttle.location_id
        # and shared_loc is no longer referenced by any shuttle.
        self.assertNotEqual(shared_loc.vertical_lift_kind, "shuttle")
