"""Versioned expert curriculum; educational proposals, never measured performance."""
from dataclasses import dataclass

SERVICE_ID = 'exp-018_football_intelligence'
VERSION = 'football_curriculum_v1'

@dataclass(frozen=True)
class Specialist:
    key: str
    label: str
    group: str
    objective: str
    practice: str
    observation: str
    source: str

# Content is original instruction design linked to reviewed antecedents, not a
# claim that any paper experimentally validates these exact activities.
TACTICS = 'https://doi.org/10.1038/s41467-024-45965-x'
SCANNING = 'https://doi.org/10.3389/fpsyg.2020.553813'
LOAD = 'https://doi.org/10.1136/bjsports-2016-096581'
NUTRITION = 'https://doi.org/10.1136/bjsports-2019-101961'
SLEEP = 'https://doi.org/10.1136/bjsports-2020-102025'
YOUTH = 'https://doi.org/10.1136/bjsports-2015-094962'
RETURN = 'https://doi.org/10.1136/bjsports-2016-096278'
IFAB = 'https://www.theifab.com/laws/2026-27/'

_ROWS = [
('head_coach','Director técnico','staff','Acordar un principio de juego','Dibuja dos organizaciones para el mismo objetivo e identifica quién mantiene la cobertura. Compara recursos y tiempo antes de elegir.','Explica qué señal haría cambiar de organización.',TACTICS),
('assistant_coach','Asistente técnico','staff','Coordinar una sesión compartida','Escribe objetivo, responsable y señal de inicio de cada bloque. Identifica dos tareas simultáneas que compiten por espacio.','Cada bloque tiene responsable y alternativa si falta material.',TACTICS),
('tactical_analyst','Analista táctico','staff','Separar hechos y lecturas tácticas','Describe una jugada recordada o anotada: fase, balón, apoyos visibles y decisión. Escribe dos explicaciones y qué dato falta para distinguirlas.','Distingue observación de hipótesis sin inventar posiciones.',TACTICS),
('opposition_analyst','Analista rival','staff','Preparar respuestas a escenarios','Compara dos situaciones del rival disponibles legítimamente. Anota fecha, contexto y una respuesta alternativa si cambia su organización.','La alternativa no depende de asumir que el rival repetirá su conducta.',TACTICS),
('session_designer','Diseño de sesiones','staff','Traducir una meta en tarea observable','Diseña una tarea con espacio, participantes, material y criterio observable. Prepara una variante más sencilla y una más compleja.','La suma de bloques cabe en el tiempo y comparte un objetivo.',TACTICS),
('set_pieces','Balón parado','staff','Distribuir funciones sin congestión','Dibuja un córner con lanzador, recepción, apoyo y cobertura. Señala ocupaciones incompatibles y revísalas sin bloqueos ilegales.','Cada función tiene propósito y zona compatible.',TACTICS),
('goalkeeper_coach','Entrenador de porteros','staff','Integrar al portero con el equipo','Diseña una situación de distribución y otra de protección del espacio; indica cómo coordinaría el portero con la defensa.','No duplica la carga del trabajo colectivo.',TACTICS),
('academy_coach','Formador de cantera','staff','Distribuir oportunidades de aprendizaje','Prepara una rotación de funciones para una tarea. Explica las adaptaciones por experiencia sin seleccionar talento por talla.','Todos tienen oportunidad y una consigna comprensible.',YOUTH),
('goalkeeper','Portero','defense','Leer relación balón y profundidad','En un dibujo de una jugada, marca portería, balón y última línea. Compara proteger portería y ajustar profundidad, indicando información faltante.','Justifica la opción sin inferir reacción o alcance corporal.',TACTICS),
('centre_back','Defensa central','defense','Coordinar presión y cobertura','Dibuja dos centrales ante un atacante. Alterna quién contiene y quién cubre; revisa qué ocurre si ambos salen.','Identifica el espacio que queda protegido.',TACTICS),
('full_back','Lateral','defense','Equilibrar banda y cobertura interior','Representa lateral, extremo y central. Compara cerrar dentro o acompañar la banda según la orientación del balón.','Explica qué compañero compensa cada alternativa.',TACTICS),
('wing_back','Carrilero','defense','Coordinar amplitud y retorno','Dibuja tres momentos: apoyo, pérdida y reorganización. Revisa si las posiciones sucesivas son plausibles sin exigir esfuerzos máximos.','Cada cambio conserva una cobertura acordada.',TACTICS),
('defensive_midfielder','Pivote defensivo','defense','Proteger líneas interiores','Marca dos líneas de pase y el apoyo del central. Compara proteger el carril y acercarse al receptor.','Reconoce qué espacio abandonaría cada opción.',SCANNING),
('build_up','Salida de balón','defense','Crear apoyos ante presión','Construye en papel dos salidas desde el portero: una corta y una alternativa. Señala receptor, apoyo siguiente y posible pérdida.','Cada pase tiene receptor visible y alternativa.',TACTICS),
('defensive_line','Línea defensiva','defense','Coordinar altura de la línea','Representa balón, portero y defensores. Compara sostener o retroceder según la presión sobre el portador.','No confunde un dibujo con una medición de fuera de juego.',TACTICS),
('defensive_transition','Transición defensiva','defense','Repartir funciones tras pérdida','En una situación dibujada asigna contención, cobertura y repliegue. Revisa que dos jugadores no abandonen la misma responsabilidad.','Cada función responde a una amenaza observable.',TACTICS),
('central_midfielder','Mediocentro o interior','attack','Reconocer apoyos antes de recibir','Dibuja una recepción con dos apoyos y presión. Compara orientación, descarga y cambio de dirección.','Explica opciones disponibles antes del contacto.',SCANNING),
('attacking_midfielder','Mediapunta','attack','Elegir entre giro y combinación','Representa una recepción entre líneas con apoyo cercano. Compara giro, descarga y pase filtrado sin asumir éxito.','Describe riesgo y apoyo necesario para cada opción.',TACTICS),
('winger','Extremo','attack','Coordinar amplitud y profundidad','Dibuja extremo y lateral en una banda. Alterna mantener amplitud, entrar por dentro y combinar, evitando ocupar el mismo corredor.','Cada alternativa identifica el apoyo que necesita.',TACTICS),
('striker','Delantero centro','attack','Relacionar desmarque y pase','Dibuja dos ventanas de desmarque y el instante del pase. Explica qué información temporal falta antes de juzgar la acción.','Distingue oportunidad táctica de decisión arbitral.',TACTICS),
('second_striker','Segundo delantero','attack','Complementar al compañero','Representa dos delanteros: uno apoya y otro ofrece profundidad. Invierte roles y compara espacios disponibles.','Evita duplicar funciones sin apoyo.',TACTICS),
('attacking_transition','Transición ofensiva','attack','Elegir continuidad tras recuperar','Describe una recuperación y compara progresar, apoyar o asegurar posesión según jugadores realmente observados.','No usa posiciones futuras para justificar la elección.',TACTICS),
('finishing','Finalización','attack','Separar oportunidad y ejecución','Revisa un remate descrito: zona, oposición y asistencia. Compara rematar y buscar apoyo sin convertir el resultado en prueba de habilidad.','Identifica información contextual además del gol.',TACTICS),
('scanning_decision','Exploración y decisión','attack','Reconocer señales antes de actuar','Antes de resolver un caso dibujado, enumera balón, apoyos y presión. Propón dos decisiones y explica qué señal cambia tu preferencia.','No confunde giro de cabeza con información comprendida.',SCANNING),
('physical_preparation','Preparación física','human','Conciliar calendario y disponibilidad','Anota compromisos deportivos y tiempo real disponible. Señala dónde una sesión individual duplicaría el trabajo del equipo.','Propone revisión del plan sin añadir carga automáticamente.',LOAD),
('training_load','Carga de entrenamiento','human','Registrar exposición con procedencia','Lista sesiones realmente realizadas con duración y esfuerzo percibido si lo recuerdas; deja desconocidos los datos ausentes.','Separa plan previsto y exposición real.',LOAD),
('strength_speed','Fuerza y velocidad','human','Preparar una progresión supervisada','Enumera experiencia, equipo y pruebas disponibles. Formula al preparador qué prerrequisito revisaría antes de una progresión.','No deduce fuerza ni aptitud desde una foto.',LOAD),
('recovery_sleep','Recuperación y sueño','human','Encontrar una oportunidad real de descanso','Compara horario previsto y obligaciones de hoy. Elige una ventana viable y una alternativa, distinguiendo percepción de dato de reloj.','La propuesta respeta la preferencia de descansar.',SLEEP),
('nutrition_hydration','Nutrición e hidratación','human','Organizar alimentación compatible','Revisa horario de sesión y comidas habituales. Anota tolerancia, acceso y restricciones para discutir opciones dentro del plan vigente.','No suma dos veces gasto ni modifica dietas terapéuticas.',NUTRITION),
('anthropometry_maturation','Antropometría y desarrollo','human','Decidir si una medida aporta información','Elige una pregunta concreta que una medida podría responder. Anota método, unidad y error; compara continuar sin medir.','No asigna posición ni maduración sexual desde el cuerpo.',YOUTH),
('psychology_daily_life','Motivación y vida cotidiana','human','Adaptar la meta a tu día','Nombra una barrera y una meta elegida por ti. Compara reducir la tarea, cambiar horario o hacer una pausa.','La alternativa es voluntaria y no penaliza descanso.',LOAD),
('safety_return_to_play','Seguridad y retorno','human','Preparar una revisión profesional','Recoge sólo para ti las restricciones vigentes y preguntas que necesitas aclarar con el profesional responsable.','No emite alta ni fecha segura de retorno.',RETURN),
('referee_laws','Reglas de juego','referee','Estudiar una regla con edición conocida','Elige una pregunta, localiza su apartado IFAB y explica qué dato del caso falta. Separa texto aplicable y tu interpretación.','Identifica edición y fuente sin inventar excepciones.',IFAB),
('referee_positioning','Posicionamiento arbitral','referee','Relacionar posición y campo visual','Dibuja balón, árbitro y posibles oclusiones. Compara dos zonas de observación como ejercicio retrospectivo.','No convierte distancia recorrida en calidad arbitral.',IFAB),
('assistant_referee','Árbitro asistente','referee','Distinguir posición y participación','Estudia un caso esquemático separando posición, instante de contacto y participación. Enumera qué faltaría para decidir.','No resuelve fuera de juego con un fotograma sin tiempo y geometría.',IFAB+'offside/'),
('fourth_official','Cuarto árbitro','referee','Ordenar un procedimiento','Simula una sustitución con cronología y roles; contrasta los pasos con la regla y el reglamento de competición.','Distingue simulación y acta oficial.',IFAB+'the-other-match-officials/'),
('var_training','Formación VAR','referee','Revisar alcance y evidencia','Separa decisión inicial, categoría revisable y evidencia disponible. Compara ángulos descritos sin atribuir certeza a una vista incompleta.','No presenta la formación como VAR autorizado.',IFAB+'video-assistant-referee-var-protocol/'),
('referee_fitness','Preparación física arbitral','referee','Organizar preparación con contexto','Anota próximos compromisos y exposición realizada. Prepara preguntas sobre el protocolo físico de tu categoría.','No copia marcas de otra categoría ni certifica aptitud.',LOAD),
('referee_communication','Comunicación arbitral','referee','Practicar mensajes claros','Escribe una indicación breve y una confirmación de recepción. Compara qué entiende otro interlocutor sin grabar datos personales.','Evalúa claridad y no personalidad o honestidad.',IFAB),
('referee_review','Revisión arbitral','referee','Transformar un error en aprendizaje','Separa hechos, interpretación y decisión en un caso. Registra la corrección y una pregunta para un caso distinto.','Conserva fuente y reconoce desacuerdos pendientes.',IFAB),
]
AGENTS = {f'fc.{row[0]}': Specialist(f'fc.{row[0]}', *row[1:]) for row in _ROWS}
LABEL_TO_KEY = {a.label: key for key, a in AGENTS.items()}

