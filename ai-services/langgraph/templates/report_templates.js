// ai-services/langgraph/templates/report_templates.js
// Plantillas de OnlyOffice Document Builder para diferentes tipos de servicio

const REPORT_TEMPLATES = {
    servicio_general: {
        name: "Reporte General de Servicio",
        sections: ["header", "general_info", "equipment", "observations", "recommendations", "conclusions", "footer"],
        styles: {
            title_color: [0, 51, 102],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Servicios Técnicos Especializados"
    },
    
    mantenimiento_preventivo: {
        name: "Reporte de Mantenimiento Preventivo",
        sections: ["header", "general_info", "checklist", "equipment", "measurements", "parts_used", "recommendations", "next_maintenance", "footer"],
        styles: {
            title_color: [0, 102, 51],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Mantenimiento Preventivo HORECA"
    },
    
    mantenimiento_correctivo: {
        name: "Reporte de Mantenimiento Correctivo",
        sections: ["header", "general_info", "problem_analysis", "equipment", "diagnosis", "repairs", "parts_used", "testing", "recommendations", "footer"],
        styles: {
            title_color: [153, 51, 0],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Mantenimiento Correctivo HORECA"
    },
    
    instalacion_equipo: {
        name: "Reporte de Instalación de Equipo",
        sections: ["header", "general_info", "equipment_specs", "installation_process", "testing", "training", "warranty", "recommendations", "footer"],
        styles: {
            title_color: [51, 102, 153],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Instalación de Equipos HORECA"
    },
    
    calibracion_tecnica: {
        name: "Reporte de Calibración Técnica",
        sections: ["header", "general_info", "equipment", "calibration_procedure", "measurements", "adjustments", "verification", "certificate", "footer"],
        styles: {
            title_color: [102, 51, 153],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Calibración Técnica HORECA"
    },
    
    inspeccion_tecnica: {
        name: "Reporte de Inspección Técnica",
        sections: ["header", "general_info", "equipment", "inspection_checklist", "findings", "compliance", "recommendations", "next_inspection", "footer"],
        styles: {
            title_color: [153, 102, 51],
            title_size: 16,
            section_size: 14,
            body_size: 11
        },
        logo: "PATCO - Inspección Técnica HORECA"
    }
};

function generateTemplateScript(templateType, data) {
    const template = REPORT_TEMPLATES[templateType] || REPORT_TEMPLATES.servicio_general;
    
    let script = `
builder.CreateFile("docx");
var oDocument = Api.GetDocument();
var oParagraph, oRun, oTable;

// Configurar estilos del documento
var oTitleStyle = oDocument.CreateStyle("Title", "paragraph");
oTitleStyle.GetTextPr().SetFontSize(${template.styles.title_size});
oTitleStyle.GetTextPr().SetBold(true);
oTitleStyle.GetTextPr().SetColor(${template.styles.title_color.join(', ')}, false);

var oSectionStyle = oDocument.CreateStyle("Section", "paragraph");
oSectionStyle.GetTextPr().SetFontSize(${template.styles.section_size});
oSectionStyle.GetTextPr().SetBold(true);
oSectionStyle.GetTextPr().SetColor(${template.styles.title_color.join(', ')}, false);

var oBodyStyle = oDocument.CreateStyle("Body", "paragraph");
oBodyStyle.GetTextPr().SetFontSize(${template.styles.body_size});

var oSubtitleStyle = oDocument.CreateStyle("Subtitle", "paragraph");
oSubtitleStyle.GetTextPr().SetFontSize(12);
oSubtitleStyle.GetTextPr().SetBold(true);
oSubtitleStyle.GetTextPr().SetItalic(true);

// Configurar márgenes del documento
var oDocPr = oDocument.GetDocumentPr();
oDocPr.SetPageMargins(720, 720, 720, 720); // 1 inch margins
`;
    
    // Generar secciones según plantilla
    template.sections.forEach(section => {
        script += generateSectionScript(section, data, template);
    });
    
    script += `
builder.SaveFile("docx", "${data.filename}");
builder.CloseFile();
`;
    
    return script;
}

function generateSectionScript(sectionType, data, template) {
    switch (sectionType) {
        case 'header':
            return generateHeaderSection(data, template);
        case 'general_info':
            return generateGeneralInfoSection(data);
        case 'equipment':
            return generateEquipmentSection(data);
        case 'checklist':
            return generateChecklistSection(data);
        case 'measurements':
            return generateMeasurementsSection(data);
        case 'parts_used':
            return generatePartsUsedSection(data);
        case 'observations':
            return generateObservationsSection(data);
        case 'recommendations':
            return generateRecommendationsSection(data);
        case 'conclusions':
            return generateConclusionsSection(data);
        case 'problem_analysis':
            return generateProblemAnalysisSection(data);
        case 'diagnosis':
            return generateDiagnosisSection(data);
        case 'repairs':
            return generateRepairsSection(data);
        case 'testing':
            return generateTestingSection(data);
        case 'next_maintenance':
            return generateNextMaintenanceSection(data);
        case 'footer':
            return generateFooterSection(data);
        default:
            return '';
    }
}

function generateHeaderSection(data, template) {
    return `
// ENCABEZADO DEL DOCUMENTO
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oTitleStyle);
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.AddText("${template.name.toUpperCase()}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Logo/Subtítulo
oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oParagraph.SetStyle(oSubtitleStyle);
oRun = Api.CreateRun();
oRun.AddText("${template.logo}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Línea separadora decorativa
oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.AddText("═══════════════════════════════════════════════════════════════════════════════");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
}

function generateGeneralInfoSection(data) {
    const servicio = data.structured_data?.servicio || {};
    const fsm_order = data.context?.fsm_order || {};
    
    return `
// INFORMACIÓN GENERAL
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("📋 INFORMACIÓN GENERAL");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Crear tabla de información general con bordes
oTable = Api.CreateTable(5, 2);
oTable.SetWidth("percent", 100);

// Configurar bordes de tabla
oTable.SetTableBorderTop("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 4, 0, 0, 0, 0);

// Configurar ancho de columnas
oTable.GetCell(0, 0).SetWidth("percent", 30);
oTable.GetCell(0, 1).SetWidth("percent", 70);

// Fila 1 - Orden de Servicio
oTable.GetCell(0, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Orden de Servicio:");
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("${escapeText(fsm_order.name || 'N/A')}");

// Fila 2 - Técnico
oTable.GetCell(1, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(1, 0).GetContent().GetElement(0).AddText("Técnico Responsable:");
oTable.GetCell(1, 1).GetContent().GetElement(0).AddText("${escapeText(servicio.tecnico || 'N/A')}");

// Fila 3 - Cliente
oTable.GetCell(2, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(2, 0).GetContent().GetElement(0).AddText("Cliente:");
oTable.GetCell(2, 1).GetContent().GetElement(0).AddText("${escapeText(servicio.cliente || 'N/A')}");

// Fila 4 - Ubicación
oTable.GetCell(3, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(3, 0).GetContent().GetElement(0).AddText("Ubicación:");
oTable.GetCell(3, 1).GetContent().GetElement(0).AddText("${escapeText(servicio.ubicacion || 'N/A')}");

// Fila 5 - Fecha
oTable.GetCell(4, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(4, 0).GetContent().GetElement(0).AddText("Fecha de Servicio:");
oTable.GetCell(4, 1).GetContent().GetElement(0).AddText("${escapeText(servicio.fecha_inicio || 'N/A')} - ${escapeText(servicio.fecha_fin || 'N/A')}");

oDocument.Push(oTable);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
}

function generateEquipmentSection(data) {
    const equipos = data.structured_data?.equipos || [];
    
    let equipmentScript = `
// EQUIPOS ATENDIDOS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("🔧 EQUIPOS ATENDIDOS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);
`;

    if (equipos.length === 0) {
        equipmentScript += `
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("No se registraron equipos específicos en esta conversación.");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);
`;
    } else {
        equipos.forEach((equipo, index) => {
            equipmentScript += `
// Equipo ${index + 1}
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.SetBold(true);
oRun.AddText("${index + 1}. ${escapeText(equipo.nombre || `Equipo ${index + 1}`)}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Crear tabla para detalles del equipo
oTable = Api.CreateTable(4, 2);
oTable.SetWidth("percent", 100);
oTable.SetTableBorderTop("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 1, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 1, 0, 0, 0, 0);

// Modelo
oTable.GetCell(0, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Modelo:");
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("${escapeText(equipo.modelo || 'N/A')}");

// Problema reportado
oTable.GetCell(1, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(1, 0).GetContent().GetElement(0).AddText("Problema Reportado:");
oTable.GetCell(1, 1).GetContent().GetElement(0).AddText("${escapeText(equipo.problema_reportado || 'N/A')}");

// Diagnóstico
oTable.GetCell(2, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(2, 0).GetContent().GetElement(0).AddText("Diagnóstico:");
oTable.GetCell(2, 1).GetContent().GetElement(0).AddText("${escapeText(equipo.diagnostico || 'N/A')}");

// Estado final
oTable.GetCell(3, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(3, 0).GetContent().GetElement(0).AddText("Estado Final:");
oTable.GetCell(3, 1).GetContent().GetElement(0).AddText("${escapeText(equipo.estado_final || 'N/A')}");

oDocument.Push(oTable);

// Acciones realizadas
${equipo.acciones_realizadas && equipo.acciones_realizadas.length > 0 ? `
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.SetBold(true);
oRun.AddText("Acciones Realizadas:");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

${equipo.acciones_realizadas.map((accion, i) => `
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("   • ${escapeText(accion)}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);
`).join('')}
` : ''}

// Espacio entre equipos
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
        });
    }

    equipmentScript += `
// Espacio final
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;

    return equipmentScript;
}

function generatePartsUsedSection(data) {
    const repuestos = data.structured_data?.repuestos_utilizados || [];
    
    if (repuestos.length === 0) {
        return `
// REPUESTOS Y MATERIALES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("🔩 REPUESTOS Y MATERIALES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("No se utilizaron repuestos específicos en este servicio.");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
    }
    
    let partsScript = `
// REPUESTOS Y MATERIALES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("🔩 REPUESTOS Y MATERIALES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Crear tabla de repuestos
oTable = Api.CreateTable(${repuestos.length + 1}, 3);
oTable.SetWidth("percent", 100);
oTable.SetTableBorderTop("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 2, 0, 0, 0, 0);

// Encabezados
oTable.GetCell(0, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Repuesto/Material");
oTable.GetCell(0, 1).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("Cantidad");
oTable.GetCell(0, 2).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 2).GetContent().GetElement(0).AddText("Observaciones");
`;

    repuestos.forEach((repuesto, index) => {
        partsScript += `
// Fila ${index + 1}
oTable.GetCell(${index + 1}, 0).GetContent().GetElement(0).AddText("${escapeText(repuesto.nombre || 'N/A')}");
oTable.GetCell(${index + 1}, 1).GetContent().GetElement(0).AddText("${escapeText(repuesto.cantidad || 'N/A')}");
oTable.GetCell(${index + 1}, 2).GetContent().GetElement(0).AddText("${escapeText(repuesto.observaciones || '-')}");
`;
    });

    partsScript += `
oDocument.Push(oTable);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;

    return partsScript;
}

function generateMeasurementsSection(data) {
    const mediciones = data.structured_data?.mediciones || [];
    
    if (mediciones.length === 0) {
        return `
// MEDICIONES Y PRUEBAS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("📊 MEDICIONES Y PRUEBAS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.AddText("No se registraron mediciones específicas en este servicio.");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
    }
    
    let measurementsScript = `
// MEDICIONES Y PRUEBAS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("📊 MEDICIONES Y PRUEBAS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Crear tabla de mediciones
oTable = Api.CreateTable(${mediciones.length + 1}, 4);
oTable.SetWidth("percent", 100);
oTable.SetTableBorderTop("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 4, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 2, 0, 0, 0, 0);

// Encabezados
oTable.GetCell(0, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Parámetro");
oTable.GetCell(0, 1).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("Valor");
oTable.GetCell(0, 2).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 2).GetContent().GetElement(0).AddText("Unidad");
oTable.GetCell(0, 3).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 3).GetContent().GetElement(0).AddText("Estado");
`;

    mediciones.forEach((medicion, index) => {
        measurementsScript += `
// Fila ${index + 1}
oTable.GetCell(${index + 1}, 0).GetContent().GetElement(0).AddText("${escapeText(medicion.parametro || 'N/A')}");
oTable.GetCell(${index + 1}, 1).GetContent().GetElement(0).AddText("${escapeText(medicion.valor || 'N/A')}");
oTable.GetCell(${index + 1}, 2).GetContent().GetElement(0).AddText("${escapeText(medicion.unidad || 'N/A')}");
oTable.GetCell(${index + 1}, 3).GetContent().GetElement(0).AddText("${escapeText(medicion.estado || 'N/A')}");
`;
    });

    measurementsScript += `
oDocument.Push(oTable);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;

    return measurementsScript;
}

function generateObservationsSection(data) {
    const observaciones = data.structured_data?.observaciones_tecnicas || 'Sin observaciones adicionales';
    
    return `
// OBSERVACIONES TÉCNICAS
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("📝 OBSERVACIONES TÉCNICAS");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oBodyStyle);
oRun = Api.CreateRun();
oRun.AddText("${escapeText(observaciones)}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
}

function generateRecommendationsSection(data) {
    const recomendaciones = data.structured_data?.recomendaciones || 'Sin recomendaciones específicas';
    
    return `
// RECOMENDACIONES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("💡 RECOMENDACIONES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oBodyStyle);
oRun = Api.CreateRun();
oRun.AddText("${escapeText(recomendaciones)}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
}

function generateConclusionsSection(data) {
    const structured_data = data.structured_data || {};
    
    return `
// CONCLUSIONES
oParagraph = Api.CreateParagraph();
oParagraph.SetStyle(oSectionStyle);
oRun = Api.CreateRun();
oRun.AddText("✅ CONCLUSIONES");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Crear tabla de conclusiones
oTable = Api.CreateTable(3, 2);
oTable.SetWidth("percent", 100);
oTable.SetTableBorderTop("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderBottom("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderLeft("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderRight("single", 2, 0, 0, 0, 0);
oTable.SetTableBorderInsideH("single", 1, 0, 0, 0, 0);
oTable.SetTableBorderInsideV("single", 1, 0, 0, 0, 0);

// Trabajo completado
oTable.GetCell(0, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("Trabajo Completado:");
oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("${structured_data.trabajo_completado ? 'Sí' : 'No'}");

// Cliente satisfecho
oTable.GetCell(1, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(1, 0).GetContent().GetElement(0).AddText("Cliente Satisfecho:");
oTable.GetCell(1, 1).GetContent().GetElement(0).AddText("${escapeText(String(structured_data.cliente_satisfecho || 'Pendiente'))}");

// Próxima visita
oTable.GetCell(2, 0).GetContent().GetElement(0).GetRun(0).SetBold(true);
oTable.GetCell(2, 0).GetContent().GetElement(0).AddText("Próxima Visita Requerida:");
oTable.GetCell(2, 1).GetContent().GetElement(0).AddText("${structured_data.proxima_visita_requerida ? 'Sí' : 'No'}");

oDocument.Push(oTable);

${structured_data.fecha_proxima_visita ? `
oParagraph = Api.CreateParagraph();
oRun = Api.CreateRun();
oRun.SetBold(true);
oRun.AddText("Fecha Próxima Visita: ");
oParagraph.AddElement(oRun);
oRun = Api.CreateRun();
oRun.AddText("${escapeText(structured_data.fecha_proxima_visita)}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);
` : ''}

// Espacio
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
`;
}

function generateFooterSection(data) {
    return `
// PIE DE DOCUMENTO
oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.AddText("═══════════════════════════════════════════════════════════════════════════════");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oParagraph.SetStyle(oSubtitleStyle);
oRun = Api.CreateRun();
oRun.SetItalic(true);
oRun.AddText("Reporte generado automáticamente por PATCO IA");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

oParagraph = Api.CreateParagraph();
oParagraph.SetJc("center");
oRun = Api.CreateRun();
oRun.SetFontSize(9);
oRun.AddText("Fecha de generación: ${new Date().toLocaleString('es-PE', { timeZone: 'America/Lima' })}");
oParagraph.AddElement(oRun);
oDocument.Push(oParagraph);

// Espacio para firmas
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);
oParagraph = Api.CreateParagraph();
oDocument.Push(oParagraph);

// Tabla para firmas
oTable = Api.CreateTable(1, 2);
oTable.SetWidth("percent", 100);

oTable.GetCell(0, 0).GetContent().GetElement(0).AddText("_________________________");
oTable.GetCell(0, 0).GetContent().GetElement(1).AddText("Firma del Técnico");

oTable.GetCell(0, 1).GetContent().GetElement(0).AddText("_________________________");
oTable.GetCell(0, 1).GetContent().GetElement(1).AddText("Firma del Cliente");

oDocument.Push(oTable);
`;
}

// Función auxiliar para escapar texto
function escapeText(text) {
    if (typeof text !== 'string') {
        return String(text || 'N/A');
    }
    return text.replace(/"/g, '\\"').replace(/'/g, "\\'").replace(/\n/g, ' ').replace(/\r/g, ' ');
}

// Exportar funciones para uso en el generador de reportes
module.exports = {
    REPORT_TEMPLATES,
    generateTemplateScript,
    generateSectionScript,
    escapeText
};