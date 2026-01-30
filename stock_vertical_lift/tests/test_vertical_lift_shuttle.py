from odoo.exceptions import ValidationError

from .common import VerticalLiftCase


class TestVerticalLiftShuttleShared(VerticalLiftCase):
    def test_shared_location_lifecycle(self):
        """Test the automated sync and constraints of shared storage."""
        # Verify auto-sync on primary location change
        self.shuttle.location_id = self.location_1b
        self.assertEqual(self.shuttle.shared_storage_location_id, self.location_1b)

        # Verify manual override logic
        self.shuttle.use_shared_storage_location = True
        self.shuttle.shared_storage_location_id = self.location_2a
        self.assertEqual(self.shuttle.shared_storage_location_id, self.location_2a)

        # Verify reset to location_id when unchecked
        self.shuttle.use_shared_storage_location = False
        self.assertEqual(self.shuttle.shared_storage_location_id, self.location_1b)

        # Verify constraint on invalid configuration
        with self.assertRaises(ValidationError):
            self.shuttle.write(
                {
                    "use_shared_storage_location": True,
                    "shared_storage_location_id": False,
                }
            )
