from odoo import models, fields, _
import logging

_logger = logging.getLogger(__name__)


class FsmPerson(models.Model):
    _inherit = 'fsm.person'

    x_employee_id = fields.Many2one('hr.employee', string='Employee')

    def action_update_from_employee(self):
        for worker in self:
            emp = worker.x_employee_id
            if not emp:
                continue
            partner = getattr(emp, 'work_contact_id', False) or getattr(emp.user_id, 'partner_id', False) or getattr(emp.company_id, 'partner_id', False)
            if not partner:
                partner = self.env['res.partner'].create({'name': emp.name or _('Employee')})
                _logger.info('Created fallback partner %s for employee %s', partner.id, emp.id)
            vals = {
                'name': emp.name,
                'partner_id': partner.id,
                'phone': getattr(emp, 'work_phone', False),
                'mobile': getattr(emp, 'mobile_phone', False),
                'email': getattr(emp, 'work_email', False),
                'active': True,
            }
            worker.write(vals | {'x_employee_id': emp.id})
        return True