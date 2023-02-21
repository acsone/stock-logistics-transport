# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    toursolver_task_id = fields.Many2one(comodel_name="toursolver.task", readonly=True)

    @api.model
    def _get_compute_picking_to_plan_ids_depends(self):
        return super()._get_compute_picking_to_plan_ids_depends() + [
            "toursolver_task_id",
            "toursolver_task_id.state",
        ]

    def _compute_can_be_planned_in_shipment_advice(self):
        res = super()._compute_can_be_planned_in_shipment_advice()
        for rec in self:
            rec.can_be_planned_in_shipment_advice = (
                rec.can_be_planned_in_shipment_advice
                and (
                    not rec.toursolver_task_id
                    or rec.toursolver_task_id.state not in ("draft", "in_progress")
                )
            )
        return res
