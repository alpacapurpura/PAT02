# ai-services/mcp/tools/report_tools.py
from typing import Dict, Any, List
import logging
import base64
from datetime import datetime
from .base import create_error_response, ErrorTypeEnum
from utils.odoo_client import OdooClient

logger = logging.getLogger(__name__)

async def create_attachment(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Crea attachment en Odoo para almacenar reporte"""
    
    try:
        # Validar argumentos requeridos
        required_fields = ['name', 'datas', 'res_model', 'res_id']
        for field in required_fields:
            if field not in arguments:
                return create_error_response(
                    ErrorTypeEnum.VALIDATION_ERROR,
                    f"Campo requerido faltante: {field}"
                )
        
        # Preparar datos del attachment
        attachment_data = {
            'name': arguments['name'],
            'datas': arguments['datas'],
            'mimetype': arguments.get('mimetype', 'application/octet-stream'),
            'res_model': arguments['res_model'],
            'res_id': arguments['res_id'],
            'description': arguments.get('description', ''),
            'x_document_type': arguments.get('x_document_type', 'report')
        }
        
        # Crear attachment usando cliente Odoo
        from server import odoo_client
        if not odoo_client:
            return create_error_response(
                ErrorTypeEnum.CONNECTION_ERROR,
                "Cliente Odoo no disponible"
            )
        
        attachment_id = await odoo_client.create('ir.attachment', attachment_data)
        
        if attachment_id:
            logger.info(f"Attachment creado exitosamente: {arguments['name']} (ID: {attachment_id})")
            return {
                "success": True,
                "attachment_id": attachment_id,
                "message": f"Attachment creado exitosamente: {arguments['name']}"
            }
        else:
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "Error creando attachment en Odoo"
            )
            
    except Exception as e:
        logger.error(f"Error creando attachment: {e}")
        return create_error_response(
            ErrorTypeEnum.INTERNAL_ERROR,
            f"Error interno: {str(e)}"
        )

async def update_fsm_order_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza orden FSM con información del reporte generado"""
    
    try:
        order_id = arguments.get('order_id')
        attachment_id = arguments.get('attachment_id')
        
        if not order_id:
            return create_error_response(
                ErrorTypeEnum.VALIDATION_ERROR,
                "order_id es requerido"
            )
        
        # Preparar datos de actualización
        update_data = {
            'x_ai_report_generated': True,
            'x_ai_report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if attachment_id:
            update_data['x_ai_report_attachment_id'] = attachment_id
        
        # Actualizar orden FSM
        from server import odoo_client
        if not odoo_client:
            return create_error_response(
                ErrorTypeEnum.CONNECTION_ERROR,
                "Cliente Odoo no disponible"
            )
        
        result = await odoo_client.write('fsm.order', [order_id], update_data)
        
        if result:
            logger.info(f"Orden FSM {order_id} actualizada con información de reporte")
            return {
                "success": True,
                "order_id": order_id,
                "message": "Orden FSM actualizada con información de reporte"
            }
        else:
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "Error actualizando orden FSM"
            )
            
    except Exception as e:
        logger.error(f"Error actualizando FSM order: {e}")
        return create_error_response(
            ErrorTypeEnum.INTERNAL_ERROR,
            f"Error interno: {str(e)}"
        )

async def get_onlyoffice_server_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Verifica estado del servidor OnlyOffice"""
    
    try:
        import requests
        
        onlyoffice_url = arguments.get('server_url', 'http://onlyoffice-documentserver:80')
        
        # Verificar health check de OnlyOffice
        response = requests.get(f"{onlyoffice_url}/healthcheck", timeout=10)
        
        if response.status_code == 200:
            logger.info(f"OnlyOffice server healthy: {onlyoffice_url}")
            return {
                "success": True,
                "status": "healthy",
                "server_url": onlyoffice_url,
                "response_time": response.elapsed.total_seconds()
            }
        else:
            logger.warning(f"OnlyOffice server unhealthy: {onlyoffice_url} - HTTP {response.status_code}")
            return {
                "success": False,
                "status": "unhealthy",
                "server_url": onlyoffice_url,
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error verificando OnlyOffice: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

async def get_conversation_for_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Obtiene información de conversación para generación de reporte"""
    
    try:
        conversation_id = arguments.get('conversation_id')
        
        if not conversation_id:
            return create_error_response(
                ErrorTypeEnum.VALIDATION_ERROR,
                "conversation_id es requerido"
            )
        
        # Obtener conversación desde Odoo
        from server import odoo_client
        if not odoo_client:
            return create_error_response(
                ErrorTypeEnum.CONNECTION_ERROR,
                "Cliente Odoo no disponible"
            )
        
        # Campos a obtener de la conversación
        conversation_fields = [
            'name', 'fsm_order_id', 'technician_id', 'channel_id', 'state',
            'current_equipment_id', 'context_data', 'conversation_summary',
            'report_template_type', 'report_generation_status'
        ]
        
        conversation_data = await odoo_client.read('ai.conversation', [conversation_id], conversation_fields)
        
        if not conversation_data:
            return create_error_response(
                ErrorTypeEnum.NOT_FOUND,
                f"Conversación {conversation_id} no encontrada"
            )
        
        conversation = conversation_data[0]
        
        # Obtener información adicional de la orden FSM
        if conversation['fsm_order_id']:
            fsm_fields = [
                'name', 'partner_id', 'location_id', 'equipment_ids',
                'x_service_nature_id', 'x_service_area_id', 'x_service_complexity_id'
            ]
            
            fsm_data = odoo_client.read('fsm.order', [conversation['fsm_order_id'][0]], fsm_fields)
            if fsm_data:
                conversation['fsm_order_details'] = fsm_data[0]
        
        # Obtener información del técnico
        if conversation['technician_id']:
            tech_fields = ['name', 'work_email', 'mobile_phone']
            tech_data = odoo_client.read('hr.employee', [conversation['technician_id'][0]], tech_fields)
            if tech_data:
                conversation['technician_details'] = tech_data[0]
        
        logger.info(f"Información de conversación {conversation_id} obtenida para reporte")
        
        return {
            "success": True,
            "conversation": conversation
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo conversación para reporte: {e}")
        return create_error_response(
            ErrorTypeEnum.INTERNAL_ERROR,
            f"Error interno: {str(e)}"
        )

async def update_conversation_report_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Actualiza el estado de generación de reporte en la conversación"""
    
    try:
        conversation_id = arguments.get('conversation_id')
        status = arguments.get('status')
        attachment_id = arguments.get('attachment_id')
        error_message = arguments.get('error_message')
        
        if not conversation_id or not status:
            return create_error_response(
                ErrorTypeEnum.VALIDATION_ERROR,
                "conversation_id y status son requeridos"
            )
        
        # Validar estado
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        if status not in valid_statuses:
            return create_error_response(
                ErrorTypeEnum.VALIDATION_ERROR,
                f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
            )
        
        # Preparar datos de actualización
        update_data = {
            'report_generation_status': status
        }
        
        if status == 'completed':
            update_data['report_generated'] = True
            update_data['state'] = 'report_generated'
            if attachment_id:
                update_data['report_attachment_id'] = attachment_id
        
        if status == 'failed' and error_message:
            update_data['report_error_message'] = error_message
        
        # Actualizar conversación
        from server import odoo_client
        if not odoo_client:
            return create_error_response(
                ErrorTypeEnum.CONNECTION_ERROR,
                "Cliente Odoo no disponible"
            )
        
        result = await odoo_client.write('ai.conversation', [conversation_id], update_data)
        
        if result:
            logger.info(f"Estado de reporte actualizado para conversación {conversation_id}: {status}")
            return {
                "success": True,
                "conversation_id": conversation_id,
                "status": status,
                "message": f"Estado de reporte actualizado a: {status}"
            }
        else:
            return create_error_response(
                ErrorTypeEnum.INTERNAL_ERROR,
                "Error actualizando estado de conversación"
            )
            
    except Exception as e:
        logger.error(f"Error actualizando estado de reporte: {e}")
        return create_error_response(
            ErrorTypeEnum.INTERNAL_ERROR,
            f"Error interno: {str(e)}"
        )