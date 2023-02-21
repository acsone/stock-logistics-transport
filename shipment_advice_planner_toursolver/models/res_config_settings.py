# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    toursolver_backend_id = fields.Many2one(
        related="company_id.toursolver_backend_id", readonly=False
    )
    toursolver_resources_number = fields.Integer(
        "Number of available resource",
        help="Resource into geoConcept must be named as D1, D2, ....",
        config_parameter="shipment_advice_planner_toursolver.toursolver_resources_number",
        default="10",
    )
