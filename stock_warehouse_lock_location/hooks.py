# Copyright 2026 Camptocamp SA
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)


def post_init_hook(env):
    """Create the Lock Location on warehouses that already exist."""
    env["stock.warehouse"].search([])._create_missing_locations({})
