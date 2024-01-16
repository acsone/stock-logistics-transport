# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.queue_job.tests.common import trap_jobs

from .common import Common


class TestShipmentAdvice(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.company_id.shipment_advice_run_in_queue_job = True
        cls.product_out4 = cls.env.ref("product.product_product_27")
        cls.group1 = cls.env["procurement.group"].create({})
        cls.group2 = cls.env["procurement.group"].create({})
        cls.group3 = cls.env["procurement.group"].create({})
        cls._update_qty_in_location(
            cls.picking_type_out.default_location_src_id,
            cls.product_out4,
            3,
        )
        cls.move1 = cls._create_move(
            cls.picking_type_out, cls.product_out4, 1, cls.group1
        )
        cls.move2 = cls._create_move(
            cls.picking_type_out, cls.product_out4, 1, cls.group2
        )
        cls.move3 = cls._create_move(
            cls.picking_type_out, cls.product_out4, 1, cls.group3
        )

    def _filter_jobs(self, jobs, method_name):
        return list(filter(lambda job: job.method_name == method_name, jobs))

    def _asset_jobs_dependency(self, jobs):
        picking_jobs = self._filter_jobs(jobs, "_validate_picking")
        unplan_job = self._filter_jobs(jobs, "_unplan_undone_moves")
        postprocess_job = self._filter_jobs(jobs, "_postprocess_action_done")
        self.assertSetEqual(postprocess_job[0].depends_on, set(unplan_job))
        self.assertSetEqual(unplan_job[0].depends_on, set(picking_jobs))

    def test_shipment_advice_incoming_done_full(self):
        """Validating an incoming shipment validates automatically planned
        transfers. Here the planned transfers have been fully received.
        """
        picking = self.move_product_in1.picking_id
        self._plan_records_in_shipment(self.shipment_advice_in, picking)
        self._in_progress_shipment_advice(self.shipment_advice_in)
        for ml in picking.move_line_ids:
            ml.qty_done = ml.reserved_uom_qty
        picking._action_done()
        with trap_jobs() as trap:
            self.shipment_advice_in.action_done()
            trap.perform_enqueued_jobs()
        self.assertEqual(self.shipment_advice_in.state, "done")
        self.assertTrue(
            all(
                move.state == "done"
                for move in self.shipment_advice_in.planned_move_ids
            )
        )
        self.assertEqual(picking.state, "done")

    def test_shipment_advice_incoming_done_partial(self):
        """Validating an incoming shipment validates automatically planned
        transfers. Here the planned transfers have been partially received.
        """
        picking = self.move_product_in1.picking_id
        # Plan a move
        self._plan_records_in_shipment(self.shipment_advice_in, self.move_product_in1)
        self._in_progress_shipment_advice(self.shipment_advice_in)
        # Receive it (making its related transfer partially received)
        for ml in self.move_product_in1.move_line_ids:
            ml.qty_done = ml.reserved_uom_qty
        self.assertEqual(picking, self.move_product_in2.picking_id)
        # When validating the shipment, a backorder is created for unprocessed moves
        with trap_jobs() as trap:
            self.shipment_advice_in.action_done()
            trap.perform_enqueued_jobs()
        backorder = self.move_product_in2.picking_id
        self.assertNotEqual(picking, backorder)
        self.assertEqual(self.shipment_advice_in.state, "done")
        self.assertEqual(self.move_product_in1.state, "done")
        self.assertEqual(picking.state, "done")
        self.assertEqual(backorder.state, "assigned")

    def test_shipment_advice_done_full(self):
        """Validating a shipment (whatever the backorder policy is) should
        validate all fully loaded transfers.
        """
        pickings = self.move1.picking_id | self.move2.picking_id | self.move3.picking_id
        self._in_progress_shipment_advice(self.shipment_advice_out)
        self._load_records_in_shipment(self.shipment_advice_out, pickings)
        with trap_jobs() as trap:
            self.shipment_advice_out.action_done()
            trap.assert_jobs_count(5)  # 3 pickings + 1 for unplan + 1 for postprocess
            jobs = trap.enqueued_jobs
            picking_jobs = self._filter_jobs(jobs, "_validate_picking")
            self.assertEqual(len(picking_jobs), 3)
            self._asset_jobs_dependency(jobs)
            trap.perform_enqueued_jobs()
        self.assertEqual(self.shipment_advice_out.state, "done")
        self.assertTrue(
            all(
                move.state == "done"
                for move in self.shipment_advice_out.loaded_move_line_ids
            )
        )
        self.assertEqual(pickings.mapped("state"), ["done", "done", "done"])

    def test_shipment_advice_done_backorder_policy_disabled(self):
        """Validating a shipment with no backorder policy should let partial
        transfers open.
        """
        # Disable the backorder policy
        company = self.shipment_advice_out.company_id
        company.shipment_advice_outgoing_backorder_policy = "leave_open"
        # Load a transfer partially (here a package)
        package_level = self.move_product_out2.move_line_ids.package_level_id
        self._in_progress_shipment_advice(self.shipment_advice_out)
        self._load_records_in_shipment(self.shipment_advice_out, package_level)
        # Validate the shipment => the transfer is still open
        with trap_jobs() as trap:
            self.shipment_advice_out.action_done()
            trap.perform_enqueued_jobs()
        picking = package_level.picking_id
        self.assertEqual(self.shipment_advice_out.state, "done")
        # Check the transfer
        self.assertTrue(
            all(
                move_line.state == "assigned"
                for move_line in package_level.move_line_ids
            )
        )
        self.assertEqual(picking.state, "assigned")

    def test_shipment_advice_done_backorder_policy_enabled(self):
        """Validating a shipment with the backorder policy enabled should
        validate partial transfers and create a backorder.
        """
        # Enable the backorder policy
        company = self.shipment_advice_out.company_id
        company.shipment_advice_outgoing_backorder_policy = "create_backorder"
        # Load a transfer partially (here a package)
        package_level = self.move_product_out2.move_line_ids.package_level_id
        self._in_progress_shipment_advice(self.shipment_advice_out)
        self._load_records_in_shipment(self.shipment_advice_out, package_level)
        self.assertEqual(package_level.picking_id, self.move_product_out1.picking_id)
        # Validate the shipment => the transfer is validated, creating a backorder
        with trap_jobs() as trap:
            self.shipment_advice_out.action_done()
            trap.perform_enqueued_jobs()
        self.assertEqual(self.shipment_advice_out.state, "done")
        # Check the transfer validated
        picking = package_level.picking_id
        self.assertTrue(
            all(move_line.state == "done" for move_line in package_level.move_line_ids)
        )
        self.assertEqual(picking.state, "done")
        # Check the backorder
        picking2 = self.move_product_out1.picking_id
        self.assertNotEqual(picking, picking2)
        self.assertTrue(
            all(move_line.state == "assigned" for move_line in picking2.move_line_ids)
        )
        self.assertEqual(picking2.state, "assigned")
