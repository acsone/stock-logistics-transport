# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ToursolverResource(models.Model):

    _name = "toursolver.resource"
    _description = "Toursolver Resource"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    toursolver_backend_id = fields.Many2one(
        comodel_name="toursolver.backend",
        string="TourSolver Backend",
        required=True,
    )
    resource_id = fields.Char(string="ResourceId", required=True)
    resource_properties = fields.Properties(
        "Properties",
        definition="toursolver_backend_id.resource_properties_definition",
        copy=True,
    )
    use_delivery_person_coordinates_as_end = fields.Boolean(
        help="If true the computed delivery will end at the delivery person's "
        "address. Otherwise it will end at the warehouse address"
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")

    def _get_resource_properties(self):
        self.ensure_one()
        return {p.get("string"): p.get("value") for p in self.resource_properties}
