# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestShipmentAdvicePlanner(TransactionCase):
    def test_shipment_advice_planner(self):
        pickings = self.env["stock.picking"].search([])
        context = {
            "active_ids": pickings.ids,
            "active_model": "stock.picking",
        }
        self.assertEqual(len(pickings), 31)
        wizard_form = Form(self.env["shipment.advice.planner"].with_context(**context))
        self.assertEqual(len(wizard_form.picking_to_plan_ids), 10)

        wizard = wizard_form.save()
        action = wizard.button_plan_shipments()
        shipments = self.env[action.get("res_model")].search(action.get("domain"))
        self.assertEqual(len(shipments), 2)
        self.assertEqual(
            shipments.mapped("warehouse_id"), pickings.mapped("warehouse_id")
        )
