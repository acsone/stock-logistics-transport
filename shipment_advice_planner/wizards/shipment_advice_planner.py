# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models


class ShipmentAdvicePlanner(models.TransientModel):
    _name = "shipment.advice.planner"
    _description = "Shipment Advice Planner"

    picking_to_plan_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Pickings to plan",
        required=True,
        domain=[("can_be_planned_in_shipment_advice", "=", True)],
        compute="_compute_picking_to_plan_ids",
        store=True,
        readonly=False,
    )
    shipment_planning_method = fields.Selection(
        selection=[("simple", "Simple")], required=True, default="simple"
    )

    @api.model
    def _get_compute_picking_to_plan_ids_depends(self):
        return ["shipment_planning_method"]

    @api.depends(lambda m: m._get_compute_picking_to_plan_ids_depends())
    def _compute_picking_to_plan_ids(self):
        """meant to be inherited if for specific method picking to plan should have
        a default record set"""
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        if not active_ids or active_model != "stock.picking":
            return self.update({"picking_to_plan_ids": False})
        pickings = self.env[active_model].browse(active_ids)
        pickings_to_plan = pickings.filtered("can_be_planned_in_shipment_advice")
        return self.update({"picking_to_plan_ids": [Command.set(pickings_to_plan.ids)]})

    def button_plan_shipments(self):
        self.ensure_one()
        shipment_advices = self._plan_shipments_for_method()
        if not shipment_advices:
            return {}
        return {
            "type": "ir.actions.act_window",
            "name": _("Shipment Advice"),
            "view_mode": "tree,form",
            "res_model": shipment_advices._name,
            "domain": [("id", "in", shipment_advices.ids)],
            "context": self.env.context,
        }

    def _plan_shipments_for_method(self):
        self.ensure_one()
        prepare_method_name = self._get_prepare_method_name()
        if not hasattr(self, prepare_method_name):
            raise NotImplementedError(
                _("There is no implementation for the planning method '%s'")
                % self.shipment_planning_method
            )
        prepare_method = getattr(self, prepare_method_name)
        shipment_advice_model = self.env["shipment.advice"]
        create_vals = []
        for (
            warehouse,
            pickings_to_plan,
        ) in self._get_picking_to_plan_by_warehouse().items():
            create_vals.extend(prepare_method(warehouse, pickings_to_plan))
        return shipment_advice_model.create(create_vals)

    def _get_prepare_method_name(self):
        return f"_prepare_shipment_advice_{self.shipment_planning_method}_vals_list"

    def _get_picking_to_plan_by_warehouse(self):
        self.ensure_one()
        warehouse_model = self.env["stock.warehouse"]
        picking_model = self.env["stock.picking"]
        res = {}
        for group in picking_model.read_group(
            [("id", "in", self.picking_to_plan_ids.ids)],
            ["warehouse_id"],
            ["warehouse_id"],
        ):
            warehouse = warehouse_model.browse(group.get("warehouse_id")[0])
            res[warehouse] = picking_model.search(group.get("__domain"))
        return res

    def _prepare_shipment_advice_simple_vals_list(self, warehouse, pickings_to_plan):
        self.ensure_one()
        vals = self._prepare_shipment_advice_common_vals(warehouse)
        vals["planned_move_ids"] = [Command.set(pickings_to_plan.move_ids.ids)]
        return [vals]

    def _prepare_shipment_advice_common_vals(self, warehouse):
        self.ensure_one()
        return {
            "shipment_type": "outgoing",
            "warehouse_id": warehouse.id,
            "company_id": warehouse.company_id.id,
        }
