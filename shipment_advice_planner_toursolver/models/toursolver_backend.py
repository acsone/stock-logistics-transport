# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class TourSolverBackend(models.Model):
    _name = "toursolver.backend"
    _description = "TourSolver Backend"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    resource_properties_definition = fields.PropertiesDefinition(
        string="Resource Properties"
    )
    url = fields.Char()
    api_key = fields.Char()
    delivery_window_disabled = fields.Boolean()
    delivery_window_start = fields.Float(default=8.0)
    delivery_window_end = fields.Float(default=17.0)
    delivery_duration = fields.Integer(
        string="Fixed time spent delivering a customer",
        help="Duration in seconds needed to deliver a customer",
        default=180,
    )
    duration = fields.Integer(
        string="Optimization process max duration",
        help="Duration in seconds allowed to the computation of the optimization",
    )
    loading_duration = fields.Integer(
        string="Fixed initial loading time", help="Loading time in minutes"
    )
    work_penalty = fields.Float(
        "Fixed cost working/hour", help="The cost of a resource working for an hour."
    )
    travel_penalty = fields.Float(
        "Fixed cost travelling/hour",
        help="The cost for a resource of driving for one distance unit.",
    )

    def _get_partner_delivery_duration(self, partner):
        self.ensure_one()
        return (
            partner.toursolver_delivery_duration
            if partner.toursolver_delivery_duration
            else self.delivery_duration
        )

    def _get_work_start_time(self):
        """
        Return the start time of the delivery rounds to geo-optimize.

        The start time is now + the geo optimization duration
        """
        self.ensure_one()
        tz_name = self.env.context.get("tz") or self.env.user.tz
        if not tz_name:
            raise UserError(
                _("Please configure your timezone in your user preferences")
            )
        m, s = divmod(self.duration, 60)
        now = fields.Datetime.context_timestamp(self, datetime.now())
        return now + timedelta(minutes=m, seconds=s)

    def _get_work_start_time_formatted(self):
        return self._get_work_start_time().strftime("%H:%M:00")

    def _get_loading_duration_formatted(self):
        h, m = divmod(self.loading_duration, 60)
        return f"{h:02d}:{m:02d}:00"
