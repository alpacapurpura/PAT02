# ai-services/langgraph/nodes/report_generator.py
import logging
from typing import Dict, Any, List
import google.generativeai as genai
import requests
import json
import os
from datetime import datetime
import tempfile
import base64
import asyncio

logger = logging.getLogger(__name__)

async def generate_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Genera reporte técnico desde conversación usando OnlyOffice"""
    
    try:
        conversation_history = state.get("messages", [])
        context = state.get("context", {})
        
        if not conversation_history:
            logger.warning("No hay historial de conversación para generar reporte")
            return state
        
        # Extraer información estructurada
        structured_data = await extract_structured_info(conversation_history, context)
        
        # Seleccionar plantilla según tipo de servicio
        template_type = determine_template_type(context, structured_data)
        
        # Generar documento con OnlyOffice Document Builder
        document_result = await create_onlyoffice_document(
            structured_data, 
            context, 
            template_type
        )
        
        # Almacenar documento en Odoo usando MCP
        attachment_id = await store_document_in_odoo(
            document_result["content"],
            document_result["filename"],
            context
        )
        
        # Actualizar estado
        state["report_generated"] = True
        state["report_attachment_id"] = attachment_id
        state["report_filename"] = document_result["filename"]
        state["structured_data"] = structured_data
        state["template_type"] = template_type
        
        logger.info(f"Reporte OnlyOffice generado exitosamente: {document_result['filename']}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error generando reporte OnlyOffice: {e}")
        state["report_generated"] = False
        state["report_error"] = str(e)
        return state

def determine_template_type(context: Dict[str, Any], structured_data: Dict[str, Any]) -> str:
    """Determina el tipo de plantilla según el contexto del servicio"""
    
    # Obtener naturaleza del servicio desde contexto
    service_nature = context.get("service_nature", "")
    equipment_category = context.get("equipment_category", "")
    
    # Mapeo de tipos de servicio a plantillas
    template_mapping = {
        "preventivo": "mantenimiento_preventivo",
        "correctivo": "mantenimiento_correctivo", 
        "instalacion": "instalacion_equipo",
        "calibracion": "calibracion_tecnica",
        "inspeccion": "inspeccion_tecnica"
    }
    
    # Determinar plantilla por naturaleza de servicio
    for key, template in template_mapping.items():
        if key.lower() in service_nature.lower():
            return template
    
    # Plantilla por defecto
    return "servicio_general"

async def extract_structured_info(
    conversation_history: List[Dict], 
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Extrae información estructurada de la conversación usando Gemini"""
    
    # Concatenar toda la conversación
    full_conversation = "\n".join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
        for msg in conversation_history
    ])
    
    # Prompt para extracción estructurada
    extraction_prompt = f"""
    Analiza la siguiente conversación entre un técnico y un asistente IA durante un servicio técnico.
    Extrae la información estructurada en formato JSON.
    
    Conversación:
    {full_conversation}
    
    Extrae la siguiente información (usa null si no está disponible):
    {{
        "servicio": {{
            "fecha_inicio": "YYYY-MM-DD HH:MM",
            "fecha_fin": "YYYY-MM-DD HH:MM",
            "tecnico": "nombre del técnico",
            "cliente": "nombre del cliente",
            "ubicacion": "dirección o ubicación"
        }},
        "equipos": [
            {{
                "nombre": "nombre del equipo",
                "modelo": "modelo si se menciona",
                "problema_reportado": "descripción del problema",
                "diagnostico": "diagnóstico del técnico",
                "acciones_realizadas": ["acción 1", "acción 2"],
                "estado_final": "funcionando/reparado/pendiente/etc"
            }}
        ],
        "repuestos_utilizados": [
            {{
                "nombre": "nombre del repuesto",
                "cantidad": "cantidad usada",
                "observaciones": "observaciones si las hay"
            }}
        ],
        "mediciones": [
            {{
                "parametro": "qué se midió",
                "valor": "valor medido",
                "unidad": "unidad de medida",
                "estado": "normal/anormal/etc"
            }}
        ],
        "observaciones_tecnicas": "observaciones generales del técnico",
        "recomendaciones": "recomendaciones para el cliente",
        "trabajo_completado": true/false,
        "cliente_satisfecho": true/false/null,
        "proxima_visita_requerida": true/false,
        "fecha_proxima_visita": "YYYY-MM-DD si aplica"
    }}
    
    Responde SOLO con el JSON, sin texto adicional.
    """
    
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(extraction_prompt)
        
        # Parsear JSON
        structured_data = json.loads(response.text)
        
        return structured_data
        
    except Exception as e:
        logger.error(f"Error extrayendo información estructurada: {e}")
        return {}

async def create_onlyoffice_document(
    structured_data: Dict[str, Any], 
    context: Dict[str, Any],
    template_type: str
) -> Dict[str, str]:
    """Crea documento usando OnlyOffice Document Builder API"""
    
    try:
        # URL del servidor OnlyOffice Document Server
        onlyoffice_url = os.getenv("ONLYOFFICE_SERVER_URL", "http://onlyoffice-documentserver:80")
        
        # Generar script de Document Builder
        builder_script = generate_document_builder_script(
            structured_data, 
            context, 
            template_type
        )
        
        # Llamar a OnlyOffice Document Builder API
        response = await call_document_builder_api(onlyoffice_url, builder_script)
        
        if response["success"]:
            return {
                "content": response["document_content"],
                "filename": generate_filename(context, structured_data),
                "format": "docx"
            }
        else:
            logger.warning(f"OnlyOffice falló, usando fallback: {response['error']}")
            # Fallback: generar documento simple con contenido de texto
            return await create_fallback_document(structured_data, context)
            
    except Exception as e:
        logger.error(f"Error creando documento OnlyOffice: {e}")
        # Fallback: generar documento simple con contenido de texto
        return await create_fallback_document(structured_data, context)

def generate_document_builder_script(
    structured_data: Dict[str, Any], 
    context: Dict[str, Any],
    template_type: str
) -> str:
    """Genera script de OnlyOffice Document Builder para crear el documento"""
    
    fsm_order = context.get("fsm_order", {})
    servicio = structured_data.get("servicio", {})
    equipos = structured_data.get("equipos", [])
    
    # Escapar comillas en los datos
    def escape_quotes(text):
        if isinstance(text, str):
            return text.replace('"', '\\"').replace("'", "\\'")
        return str(text) if text is not None else "N/A"
    
    script = f'''
builder.CreateFile("docx");
var oDocument = Api.GetDocument();
var oParagraph, oRun, oTable;

// Configurar estilos del documento
var oTitleStyle = oDocument.CreateStyle("Title", "paragraph");
oTitleStyle.GetTextPr().SetFontSize(16);
oTitleStyle.GetTextPr().SetBold(true);
oTitleStyle.GetTextPr().SetColor(0, 51, 102, false);

var oSectionStyle = oDocument.CreateStyle("Section", "paragraph");
oSectionStyle.GetTextPr().SetFontSize(14);
oSectionStyle.GetTextPr().SetBold(true);

var oBodyStyle = oDocument.CreateStyle("Body", "paragraph");
oBodyStyle.GetTextPr().SetFontSize(11);

// ENCABEZADO DEL DOCUMENTO
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oTitleStyle);
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.AddText("REPORTE DE SERVICIO TÉCNICO PATCO");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Subtítulo
oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.AddText("Servicios Técnicos Especializados HORECA");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Línea separadora
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("================================================================================");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);

// INFORMACIÓN GENERAL
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("INFORMACIÓN GENERAL");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Tabla de información general
oTable = Api.CreateTable(4, 2);
oTable.SetWidth("percent", 100);

// Configurar bordes de tabla
oTable.SetTableBorderTop("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 4, 0, 0, 0, 0);

// Fila 1
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Orden de Servicio:");
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("{escape_quotes(fsm_order.get('name', 'N/A'))}");

// Fila 2
oTable.GetCell(1, 0).GetContent().GetElement(0).AddText("Técnico Responsable:");
oTable.GetCell(1, 1).GetContent().GetElement(0).AddText("{escape_quotes(servicio.get('tecnico', 'N/A'))}");

// Fila 3
oTable.GetCell(2, 0).GetContent().GetElement(0).AddText("Cliente:");
oTable.GetCell(2, 1).GetContent().GetElement(0).AddText("{escape_quotes(servicio.get('cliente', 'N/A'))}");

// Fila 4
oTable.GetCell(3, 0).GetContent().GetElement(0).AddText("Fecha de Servicio:");
oTable.GetCell(3, 1).GetContent().GetElement(0).AddText("{escape_quotes(servicio.get('fecha_inicio', 'N/A'))} - {escape_quotes(servicio.get('fecha_fin', 'N/A'))}");

oDocument.Push(oTable);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);

// EQUIPOS ATENDIDOS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("EQUIPOS ATENDIDOS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);
'''
    
    # Agregar información de equipos
    for i, equipo in enumerate(equipos):
        script += f'''
// Equipo {i+1}
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.SetBold(true);
oRun.AddText("{i+1}. {escape_quotes(equipo.get('nombre', f'Equipo {i+1}'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("   Modelo: {escape_quotes(equipo.get('modelo', 'N/A'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("   Problema Reportado: {escape_quotes(equipo.get('problema_reportado', 'N/A'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("   Diagnóstico: {escape_quotes(equipo.get('diagnostico', 'N/A'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("   Estado Final: {escape_quotes(equipo.get('estado_final', 'N/A'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio entre equipos
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
'''
    
    # Finalizar documento
    script += f'''
// OBSERVACIONES TÉCNICAS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("OBSERVACIONES TÉCNICAS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("{escape_quotes(structured_data.get('observaciones_tecnicas', 'Sin observaciones adicionales'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);

// RECOMENDACIONES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("RECOMENDACIONES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("{escape_quotes(structured_data.get('recomendaciones', 'Sin recomendaciones específicas'))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);

// CONCLUSIONES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("CONCLUSIONES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("Trabajo Completado: {'Sí' if structured_data.get('trabajo_completado') else 'No'}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("Cliente Satisfecho: {escape_quotes(str(structured_data.get('cliente_satisfecho', 'Pendiente')))}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// PIE DE DOCUMENTO
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("================================================================================");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.SetItalic(true);
oRun.AddText("Reporte generado automáticamente por PATCO IA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

builder.SaveFile("docx", "{generate_filename(context, structured_data)}");
builder.CloseFile();
'''
    
    return script

async def call_document_builder_api(onlyoffice_url: str, script: str) -> Dict[str, Any]:
    """Llama a la API de OnlyOffice Document Builder"""
    
    try:
        # Endpoint de Document Builder
        builder_url = f"{onlyoffice_url}/docbuilder"
        
        # Preparar payload
        payload = {
            "async": False,
            "filetype": "docx",
            "key": f"patco_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "outputtype": "docx",
            "script": script
        }
        
        # Headers con JWT si está habilitado
        headers = {
            "Content-Type": "application/json"
        }
        
        jwt_secret = os.getenv("ONLYOFFICE_JWT_SECRET", "patco-onlyoffice-jwt-secret-2025")
        if jwt_secret:
            try:
                import jwt
                token = jwt.encode(payload, jwt_secret, algorithm="HS256")
                headers["Authorization"] = f"Bearer {token}"
            except ImportError:
                logger.warning("PyJWT no disponible, enviando sin JWT")
        
        # Realizar llamada HTTP
        response = requests.post(
            builder_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("error") == 0:
                # Descargar documento generado
                download_url = result.get("fileUrl")
                if download_url:
                    doc_response = requests.get(download_url, timeout=30)
                    return {
                        "success": True,
                        "document_content": base64.b64encode(doc_response.content).decode(),
                        "download_url": download_url
                    }
            
            return {
                "success": False,
                "error": result.get("error", "Error desconocido en Document Builder")
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error llamando Document Builder API: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def create_fallback_document(
    structured_data: Dict[str, Any], 
    context: Dict[str, Any]
) -> Dict[str, str]:
    """Crea documento de respaldo en caso de fallo de OnlyOffice"""
    
    # Generar contenido de texto simple
    content = generate_simple_report_content(structured_data, context)
    
    # Convertir a base64 para almacenamiento
    content_b64 = base64.b64encode(content.encode('utf-8')).decode()
    
    return {
        "content": content_b64,
        "filename": generate_filename(context, structured_data, extension="txt"),
        "format": "txt"
    }

def generate_filename(
    context: Dict[str, Any], 
    structured_data: Dict[str, Any], 
    extension: str = "docx"
) -> str:
    """Genera nombre de archivo para el reporte"""
    
    fsm_order = context.get("fsm_order", {})
    order_name = fsm_order.get("name", "UNKNOWN").replace("/", "_").replace("\\", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    return f"Reporte_Servicio_{order_name}_{timestamp}.{extension}"

async def store_document_in_odoo(
    document_content: str, 
    filename: str, 
    context: Dict[str, Any]
) -> int:
    """Almacena el documento generado en Odoo como attachment usando MCP"""
    
    try:
        # URL del servidor MCP
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8080")
        
        # Preparar datos del attachment
        attachment_data = {
            "name": filename,
            "datas": document_content,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filename.endswith('.docx') else "text/plain",
            "res_model": "fsm.order",
            "res_id": context.get("fsm_order_id"),
            "x_document_type": "report",
            "description": "Reporte técnico generado automáticamente por IA"
        }
        
        # Llamar a MCP para crear attachment
        response = requests.post(
            f"{mcp_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "create_attachment",
                    "arguments": attachment_data
                },
                "id": 1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result", {}).get("success"):
                attachment_id = result["result"]["attachment_id"]
                
                # Actualizar orden FSM con información del reporte
                await update_fsm_order_with_report(context.get("fsm_order_id"), attachment_id)
                
                return attachment_id
            else:
                raise Exception(f"Error en MCP: {result.get('result', {}).get('error', 'Error desconocido')}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        logger.error(f"Error almacenando documento en Odoo: {e}")
        raise

async def update_fsm_order_with_report(order_id: int, attachment_id: int):
    """Actualiza la orden FSM con información del reporte generado"""
    
    try:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8080")
        
        response = requests.post(
            f"{mcp_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "update_fsm_order_report",
                    "arguments": {
                        "order_id": order_id,
                        "attachment_id": attachment_id
                    }
                },
                "id": 1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if not result.get("result", {}).get("success"):
                logger.warning(f"No se pudo actualizar orden FSM: {result.get('result', {}).get('error')}")
        else:
            logger.warning(f"Error actualizando orden FSM: HTTP {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error actualizando orden FSM: {e}")

def generate_simple_report_content(
    structured_data: Dict[str, Any], 
    context: Dict[str, Any]
) -> str:
    """Genera contenido de reporte simple como fallback"""
    
    fsm_order = context.get("fsm_order", {})
    servicio = structured_data.get("servicio", {})
    equipos = structured_data.get("equipos", [])
    
    content = f"""
REPORTE DE SERVICIO TÉCNICO PATCO
{'='*50}

INFORMACIÓN GENERAL
Orden de Servicio: {fsm_order.get('name', 'N/A')}
Técnico: {servicio.get('tecnico', 'N/A')}
Cliente: {servicio.get('cliente', 'N/A')}
Fecha: {servicio.get('fecha_inicio', 'N/A')} - {servicio.get('fecha_fin', 'N/A')}
Ubicación: {servicio.get('ubicacion', 'N/A')}

EQUIPOS ATENDIDOS
{'-'*20}
"""
    
    for i, equipo in enumerate(equipos, 1):
        content += f"""
{i}. {equipo.get('nombre', f'Equipo {i}')}
   Modelo: {equipo.get('modelo', 'N/A')}
   Problema: {equipo.get('problema_reportado', 'N/A')}
   Diagnóstico: {equipo.get('diagnostico', 'N/A')}
   Estado Final: {equipo.get('estado_final', 'N/A')}
"""
    
    content += f"""
OBSERVACIONES TÉCNICAS
{'-'*25}
{structured_data.get('observaciones_tecnicas', 'Sin observaciones adicionales')}

RECOMENDACIONES
{'-'*15}
{structured_data.get('recomendaciones', 'Sin recomendaciones específicas')}

CONCLUSIONES
{'-'*12}
Trabajo Completado: {'Sí' if structured_data.get('trabajo_completado') else 'No'}
Cliente Satisfecho: {structured_data.get('cliente_satisfecho', 'Pendiente')}

{'='*50}
Reporte generado automáticamente por PATCO IA
Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return content