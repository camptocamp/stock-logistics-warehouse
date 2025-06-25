# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class VerticalLiftOperationPickZeroCheck(models.TransientModel):
    _name = "vertical.lift.operation.pick.zero.check"
    _description = "Make sure the tray location is empty"

    vertical_lift_operation_pick_id = fields.Many2one("vertical.lift.operation.pick")

    def _get_data_from_operation(self):
        """Return picking, location and product from the operation shuttle"""
        operation = self.vertical_lift_operation_pick_id

        # If the move is split into several move lines, it is
        # moved to another picking, being a backorder of the
        # original one. We are always interested in the original
        # picking that was processed at first, so if the picking
        # is a backorder of another picking, we take that other one.
        # picking = operation.picking_id.backorder_id or operation.picking_id
        location = operation.current_move_line_id.location_id
        package = operation.current_move_line_id.package_id
        lot = operation.current_move_line_id.lot_id
        product = operation.product_id
        return location, product, package, lot

    def _update_empty_inventory(self):
        quants = self.get_existing_quant()
        if quants:
            for quant in quants:
                if quant.inventory_quantity_set:
                    continue
                quant.write(
                    {
                        # Set a user to prevent the zero quant cleanup
                        "user_id": self.env.user.id,
                        "inventory_quantity": 0,
                        "inventory_date": fields.Date.today(),
                    }
                )
            return quants

    def _create_draft_inventory(self):
        location, product, package, lot = self._get_data_from_operation()
        quants = self._update_empty_inventory()
        if quants is None:
            # Only create a new quant if there is no existing one
            quants = (
                self.env["stock.quant"]
                .sudo()
                .create(
                    {
                        "location_id": location.id,
                        "product_id": product.id,
                        "lot_id": lot.id,
                        "inventory_quantity": 1,
                        "inventory_date": fields.Date.today(),
                        "package_id": package.id if package else False,
                    }
                )
            )
        return quants

    def get_existing_quant(self, limit=1):
        location, product, package, lot = self._get_data_from_operation()
        domain = [("location_id", "=", location.id), ("product_id", "=", product.id)]
        if package is not None:
            domain.append(("package_id", "=", package.id))
        else:
            domain.append(("package_id", "=", False))
        if lot is not None:
            domain.append(("lot_id", "=", lot.id))
        else:
            domain.append(("lot_id", "=", False))
        return self.env["stock.quant"].search(domain, limit=limit)

    def button_confirm_empty(self):
        """User confirms the tray location is empty

        This is in accordance with what we expected, because we only
        call this action if we think the location is empty. We create
        an inventory adjustment that states that a zero-check was
        done for this location."""
        # inventory_name = self.env._(
        # f"Zero check in location: {location.complete_name}")
        # inventory = (
        #     self.env["stock.inventory"]
        #     .sudo()
        #     .create(
        #         {
        #             "name": inventory_name,
        #             "product_ids": [(4, product.id)],
        #             "location_ids": [(4, location.id)],
        #             "line_ids": [
        #                 (
        #                     0,
        #                     0,
        #                     {
        #                         "product_id": product.id,
        #                         "product_qty": 0,
        #                         "theoretical_qty": 0,
        #                         "location_id": location.id,
        #                     },
        #                 ),
        #             ],
        #         }
        #     )
        # )
        self._update_empty_inventory()

        # Return to the execution of the release,
        # but without checking again if the tray is empty.
        return self.vertical_lift_operation_pick_id.with_context(
            skip_zero_quantity_check=True
        ).button_release()

    def button_confirm_not_empty(self):
        """User confirms the tray location is not empty

        This contradicts what we expected, because we only call this
        action if we think the location is empty. We create a draft
        inventory adjustment stating the mismatch.
        """
        # inventory_name = self.env._(
        #     f"{picking.name} zero check issue on location {location.complete_name}"
        # )
        # self.env["stock.inventory"].sudo().create(
        #     {
        #         "name": inventory_name,
        #         "product_ids": [(4, product.id)],
        #         "location_ids": [(4, location.id)],
        #     }
        # )
        self._create_draft_inventory()

        # Return to the execution of the release,
        # but without checking again if the tray is empty.
        return self.vertical_lift_operation_pick_id.with_context(
            skip_zero_quantity_check=True
        ).button_release()
