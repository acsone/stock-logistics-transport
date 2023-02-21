# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    toursolver_delivery_window_ids = fields.One2many(
        comodel_name="toursolver.delivery.window",
        inverse_name="partner_id",
        string="Delivery windows",
        help="If specified, delivery is only possible into the specified "
        "time windows. (Leaves empty if no restriction)",
    )
    toursolver_delivery_duration = fields.Integer()

    def _get_delivery_windows(self, day_name):
        """
        Return the list of delivery windows by partner id for the given day.

        :param day: The day name (see toursolver.delivery.week.day)
        :return: dict partner_id:[delivery_window, ]
        """
        self.ensure_one()
        week_day_id = self.env["toursolver.delivery.week.day"]._get_id_by_name(day_name)
        return self.env["toursolver.delivery.window"].search(
            [("partner_id", "=", self.id), ("week_day_ids", "in", week_day_id)]
        )

    def _get_delivery_sequence(self, day_name):
        """
        Return a sequence position by partner id for the given day.

        The sequence is computed from the delivery_widow start

        :param day: The day name (see toursolver.delivery.week.day)
        :return: dict partner_id:sequence
        """
        week_day_id = self.env["toursolver.delivery.week.day"]._get_id_by_name(day_name)
        res = {}
        windows = self.env["toursolver.delivery.window"].search(
            [("partner_id", "in", self.ids), ("week_day_ids", "in", week_day_id)],
            order="start ASC",
        )
        i = 1
        for window in windows.sorted("start"):
            if window.partner_id.id not in res:
                res[window.partner_id.id] = i
                i += 1
        for partner in self.sorted("name"):
            if partner.id not in res:
                res[partner.id] = i
                i += 1
        return res
