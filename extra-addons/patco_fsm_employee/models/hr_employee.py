from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_is_fsm_worker = fields.Boolean(string='FSM Worker')
    x_fsm_person_id = fields.Many2one('fsm.person', string='FSM Worker')

    def _get_partner_for_employee(self):
        for emp in self:
            partner = getattr(emp, 'work_contact_id', False) or getattr(emp.user_id, 'partner_id', False) or getattr(emp, 'company_id', False) and emp.company_id.partner_id
            if not partner:
                partner = self.env['res.partner'].create({'name': emp.name or _('Employee')})
                _logger.info('Created fallback partner %s for employee %s', partner.id, emp.id)
            yield emp, partner

    def _build_fsm_vals(self, emp, partner):
        phone = getattr(emp, 'work_phone', False)
        mobile = getattr(emp, 'mobile_phone', False)
        email = getattr(emp, 'work_email', False)
        return {
            'name': emp.name,
            'partner_id': partner.id if partner else False,
            'phone': phone,
            'mobile': mobile,
            'email': email,
            'active': True,
        }

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for emp in employees:
            if emp.x_is_fsm_worker and not emp.x_fsm_person_id:
                for _emp, partner in emp._get_partner_for_employee():
                    # Reusar existente si está vinculado por empleado o partner
                    fsm = self.env['fsm.person'].search([('x_employee_id', '=', emp.id)], limit=1) or \
                          self.env['fsm.person'].search([('partner_id', '=', partner.id)], limit=1)
                    if fsm:
                        fsm.write(self._build_fsm_vals(emp, partner))
                    else:
                        fsm = self.env['fsm.person'].create({**self._build_fsm_vals(emp, partner), 'x_employee_id': emp.id})
                    emp.x_fsm_person_id = fsm.id
        return employees

    def action_sync_to_fsm(self):
        for emp in self:
            for _emp, partner in emp._get_partner_for_employee():
                fsm = emp.x_fsm_person_id or \
                      self.env['fsm.person'].search([('x_employee_id', '=', emp.id)], limit=1) or \
                      self.env['fsm.person'].search([('partner_id', '=', partner.id)], limit=1)
                vals = self._build_fsm_vals(emp, partner)
                if fsm:
                    fsm.write(vals | {'x_employee_id': emp.id})
                else:
                    fsm = self.env['fsm.person'].create(vals | {'x_employee_id': emp.id})
                emp.write({'x_fsm_person_id': fsm.id, 'x_is_fsm_worker': True})
        return True