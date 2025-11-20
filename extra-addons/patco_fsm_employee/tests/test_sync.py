from odoo.tests.common import TransactionCase


class TestFsmEmployeeSync(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp_model = self.env['hr.employee']
        self.fsm_model = self.env['fsm.person']
        self.partner = self.env['res.partner'].create({'name': 'John Partner'})

    def test_create_employee_creates_fsm(self):
        emp = self.emp_model.create({
            'name': 'John Employee',
            'address_home_id': self.partner.id,
            'x_is_fsm_worker': True,
        })
        self.assertTrue(emp.x_fsm_person_id, 'FSM worker should be created')
        self.assertEqual(emp.x_fsm_person_id.partner_id, self.partner)

    def test_sync_button_updates_fsm(self):
        emp = self.emp_model.create({'name': 'Jane', 'x_is_fsm_worker': False})
        emp.action_sync_to_fsm()
        self.assertTrue(emp.x_fsm_person_id)
        emp.name = 'Jane Updated'
        emp.action_sync_to_fsm()
        self.assertEqual(emp.x_fsm_person_id.name, 'Jane Updated')