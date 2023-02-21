# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestToursolverDeliveryWindow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_window_model = cls.env["toursolver.delivery.window"]
        cls.partner_model = cls.env["res.partner"]
        cls.partner_1 = cls.partner_model.create({"name": "partner 1"})
        cls.partner_2 = cls.partner_model.create({"name": "patner 2"})
        cls.monday = cls.env.ref(
            "shipment_advice_planner_toursolver.toursolver_delivery_weed_day_monday"
        )
        cls.sunday = cls.env.ref(
            "shipment_advice_planner_toursolver.toursolver_delivery_weed_day_sunday"
        )

    def test_00(self):
        """
        Data:

            A partner without delivery window
        Test Case:
            Add a delivery window
        Expected result:
            A delivery window is created for the partner
        """

        self.assertFalse(self.partner_1.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        self.assertTrue(self.partner_1.toursolver_delivery_window_ids)
        delivery_window = self.partner_1.toursolver_delivery_window_ids
        self.assertEqual(delivery_window.start, 10.0)
        self.assertEqual(delivery_window.end, 12.0)
        self.assertEqual(delivery_window.week_day_ids, self.monday)

    def test_01(self):
        """
        Data:

            A partner without delivery window
        Test Case:
            1 Add a delivery window
            2 unlink the partner
        Expected result:
            1 A delivery window is created for the partner
            2 The delivery window is removed
        """
        partner_id = self.partner_1.id
        self.assertFalse(self.partner_1.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        self.assertTrue(self.partner_1.toursolver_delivery_window_ids)
        delivery_window = self.delivery_window_model.search(
            [("partner_id", "=", partner_id)]
        )
        self.assertTrue(delivery_window)
        self.partner_1.unlink()
        self.assertFalse(delivery_window.exists())

    def test_02(self):
        """
        Data:

            A partner without delivery window
        Test Case:
            1 Add a delivery window
            2 Add a second delivery window that overlaps the first one (same day)
        Expected result:
            1 A delivery window is created for the partner
            2 ValidationError is raised
        """
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        with self.assertRaises(ValidationError):
            self.delivery_window_model.create(
                {
                    "partner_id": self.partner_1.id,
                    "start": 11.0,
                    "end": 13.0,
                    "week_day_ids": [(4, self.monday.id), (4, self.sunday.id)],
                }
            )

    def test_03(self):
        """
        Data:

            A partner without delivery window
        Test Case:
            1 Add a delivery window
            2 Add a second delivery window that overlaps the first one (another day)
        Expected result:
            1 A delivery window is created for the partner
            2 A second  delivery window is created for the partner
        """
        self.assertFalse(self.partner_1.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        self.assertTrue(self.partner_1.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 11.0,
                "end": 13.0,
                "week_day_ids": [(4, self.sunday.id)],
            }
        )
        self.assertEqual(len(self.partner_1.toursolver_delivery_window_ids), 2)

    def test_04(self):
        """
        Data:

            Partner 1 without delivery window
            Partner 2 without delivery window
        Test Case:
            1 Add a delivery window to partner 1
            2 Add the same delivery window to partner 2
        Expected result:
            1 A delivery window is created for the partner 1
            1 A delivery window is created for the partner 2
        """
        self.assertFalse(self.partner_1.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_1.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        self.assertTrue(self.partner_1.toursolver_delivery_window_ids)
        self.assertFalse(self.partner_2.toursolver_delivery_window_ids)
        self.delivery_window_model.create(
            {
                "partner_id": self.partner_2.id,
                "start": 10.0,
                "end": 12.0,
                "week_day_ids": [(4, self.monday.id)],
            }
        )
        self.assertTrue(self.partner_2.toursolver_delivery_window_ids)

    def test_05(self):
        """
        Data:

            Partner 1 without delivery window
        Test Case:
            Add a delivery window to partner 1 with end > start
        Expected result:
            ValidationError is raised
        """
        with self.assertRaises(ValidationError):
            self.delivery_window_model.create(
                {
                    "partner_id": self.partner_1.id,
                    "start": 14.0,
                    "end": 12.0,
                    "week_day_ids": [(4, self.monday.id)],
                }
            )
