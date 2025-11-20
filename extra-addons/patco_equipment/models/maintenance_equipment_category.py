from odoo import models, fields, api
import base64
import zipfile
import io


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'