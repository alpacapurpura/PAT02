from odoo import models


class ReportCommon(models.AbstractModel):
    _name = 'report.patco_reports.common'
    _description = 'Common helpers for PATCO reports'

    def _get_company_bank_accounts(self, company):
        accounts = []
        for bank in company.partner_id.bank_ids:
            accounts.append({
                'bank_name': bank.bank_id and bank.bank_id.name or '',
                'acc_number': bank.acc_number or '',
                'holder_name': company.name or '',
                'currency': company.currency_id.name or '',
            })
        return accounts