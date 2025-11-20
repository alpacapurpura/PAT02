from odoo import models
import logging
import json
import requests
from urllib.parse import urljoin

_logger = logging.getLogger(__name__)


class PatcoAIClient(models.AbstractModel):
    _name = 'patco.ai.client'
    _description = 'PATCO AI Client'

    def rag_query(self, payload_json):
        try:
            data = {}
            try:
                if isinstance(payload_json, (bytes, bytearray)):
                    payload_json = payload_json.decode('utf-8')
                data = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
            except Exception:
                data = {}
            icp = self.env['ir.config_parameter'].sudo()
            base = icp.get_param('ai.rag_endpoint_base') or ''
            endpoint = icp.get_param('ai.rag_endpoint') or ''
            timeout = icp.get_param('ai.rag_timeout') or ''
            try:
                timeout = float(timeout) if timeout else 10.0
            except Exception:
                timeout = 10.0
            headers = {'Content-Type': 'application/json'}
            api_key = icp.get_param('ai.rag_api_key') or ''
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            # Build URL for LangGraph if conversation_id provided
            conversation_id = data.get('conversation_id')
            url = ''
            if conversation_id:
                if base:
                    url = urljoin(base, f"/conversation/{conversation_id}/message")
                elif endpoint:
                    url = endpoint.replace('{conversation_id}', str(conversation_id))
            else:
                url = endpoint
            if not url:
                return "Hola! No tienes ninguna orden de mantenimiento activa en estos momentos =(. Soy tu asistente técnico, cuando tengas una orden de mantenimiento, ahí estaré!"
            try:
                resp = requests.post(url, json=data, headers=headers, timeout=timeout)
                if resp.ok:
                    try:
                        j = resp.json()
                        if isinstance(j, dict):
                            if 'response' in j:
                                return str(j.get('response') or '')
                            # Fallbacks
                            if 'answer' in j:
                                return str(j.get('answer') or '')
                        return resp.text or ''
                    except Exception:
                        return resp.text or ''
                return ''
            except Exception:
                _logger.exception('patco_ai: rag_query request failed')
                return ''
        except Exception:
            _logger.exception('patco_ai: rag_query exception')
            return ''