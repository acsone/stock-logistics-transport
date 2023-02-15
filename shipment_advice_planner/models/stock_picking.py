# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", related="location_id.warehouse_id", store=True
    )
    can_be_planned_in_shipment_advice = fields.Boolean(
        compute="_compute_can_be_planned_in_shipment_advice", store=True
    )

    @api.depends("planned_shipment_advice_id", "state", "picking_type_code")
    def _compute_can_be_planned_in_shipment_advice(self):
        for rec in self:
            rec.can_be_planned_in_shipment_advice = (
                not rec.planned_shipment_advice_id
                and rec.state == "assigned"
                and rec.picking_type_code == "outgoing"
            )

    def init(self):
        self.env.cr.execute(
            """
                CREATE INDEX IF NOT EXISTS
                stock_picking_can_be_planned_in_shipment_advice_index
                ON stock_picking(can_be_planned_in_shipment_advice)
                WHERE can_be_planned_in_shipment_advice is true;
            """
        )
