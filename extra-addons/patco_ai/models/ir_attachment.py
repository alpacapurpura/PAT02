import json
from urllib.parse import urljoin
from odoo import api, fields, models
import os


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    x_is_manual_doc = fields.Boolean(string='Manual Doc (Index to RAG)', default=False)
    
    # RAG Indexing Fields
    x_is_indexed = fields.Boolean(string='Indexed', default=False, index=True)
    x_indexed_date = fields.Datetime(string='Indexed Date')
    x_indexing_error = fields.Char(string='Indexing Error')
    x_document_type = fields.Selection([
        ('manual', 'Manual'),
        ('procedure', 'Procedure'),
        ('checklist', 'Checklist'),
        ('other', 'Other')
    ], string='Document Type', default='other')
    x_content_hash = fields.Char(string='Content Hash')
    
    # Metadata for RAG Context (Stored as JSON strings)
    x_equipment_category_ids = fields.Char(string='Equipment Category IDs', compute='_compute_rag_metadata', store=True)
    x_service_nature_ids = fields.Char(string='Service Nature IDs', compute='_compute_rag_metadata', store=True)

    @api.depends('res_model', 'res_id')
    def _compute_rag_metadata(self):
        for rec in self:
            cats = []
            natures = []
            if rec.res_model == 'maintenance.equipment.category' and rec.res_id:
                cats.append(rec.res_id)
            elif rec.res_model == 'maintenance.equipment' and rec.res_id:
                # Avoid browsing if possible, but needed here
                try:
                    eq = self.env['maintenance.equipment'].browse(rec.res_id)
                    if eq.exists() and eq.category_id:
                        cats.append(eq.category_id.id)
                except Exception:
                    pass
            
            rec.x_equipment_category_ids = json.dumps(cats)
            rec.x_service_nature_ids = json.dumps(natures)

    def write(self, vals):
        # Reset indexing if content changes
        if 'datas' in vals:
            vals['x_is_indexed'] = False
            vals['x_indexing_error'] = False
        return super().write(vals)

    def _ai_client(self):
        return self.env['patco.ai.client']


class PatcoAIClient(models.AbstractModel):
    _name = 'patco.ai.client'
    _description = 'PATCO AI Client'

    def _mcp_url(self):
        env_url = os.environ.get('AI_MCP_URL')
        if env_url:
            return env_url
        cfg_url = self.env['ir.config_parameter'].sudo().get_param('ai.mcp.url')
        if cfg_url:
            return cfg_url
        running = os.environ.get('RUNNING_ENV') or self.env['ir.config_parameter'].sudo().get_param('running_env')
        if running and running.lower() in ('prod', 'production'):
            return 'https://ai.patcoperu.com'
        return 'http://ai-mcp-dev:8080'

    def _timeout(self):
        return 10

    def _post_json(self, path, payload):
        import urllib.request
        import urllib.error
        data = payload.encode('utf-8')
        req = urllib.request.Request(url=f"{self._mcp_url()}{path}", data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, timeout=self._timeout()) as resp:
                return resp.read()
        except urllib.error.URLError:
            return b''

    def rag_query(self, payload_json):
        import json
        import urllib.request
        import urllib.error

        payload = json.loads(payload_json)
        conversation_id = payload.get('conversation_id')
        
        # Get endpoint from config
        endpoint_template = self.env['ir.config_parameter'].sudo().get_param(
            'ai.rag_endpoint', 
            'http://patco-langgraph-server-dev:8001/conversation/{conversation_id}/message'
        )
        
        if not conversation_id:
            return ""

        url = endpoint_template.replace('{conversation_id}', str(conversation_id))
        
        # Remove conversation_id from payload as it's in the URL
        if 'conversation_id' in payload:
            del payload['conversation_id']
            
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url=url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=self._timeout()) as resp:
                response_data = json.loads(resp.read())
                # Extract the actual text response from the LangGraph response
                return response_data.get('response', '')
        except urllib.error.URLError as e:
            # Log the error if possible, or just return empty to trigger fallback
            return ""
        except Exception:
            return ""