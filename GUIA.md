GUIA Prueba técnica Analista Jr — Insights WM

1. Manejo de Datos: 
    En el archivo 'ManejoDatos.ipynb', se pueden encontrar los pasos uno por uno, haciendo uso de las funciones respectivas de "filter,join,drop", gracias a esto se tendra como resultado la consulta de los balances, para el rango de fechas, segun el tipo de portafolio y para los usuarios que son asesorados por insightswm@gmail.com.

2. Portafolios: 
    En el archivo '2portafolios', se encuentra la solcuion para el segundo literal de la prueba. Este es un archivo python, que retornara 2.1 en términos de P y R, el retorno esperado y la volatilidad esperada de los portafolios asociados a los pesos P1 y P2, 2.2 el retorno esperado y volatilidad esperada de ambos portafolios calculada, y por ultimo, 2.3 la comparacion de los outputs de las respuestas de Claude y Gemini en una tabla segun profundidad, precisión, tono y estructura, con una conclusion de la escogencia y su debida justificacion.

3. Caso automatizacion: 
    En la carpeta 'withdrawal-agent', el archivo 'withdrawal_engine.py', permite procesar la informacion presente en el excel withdrawals.xlsx, por medio, de este archivo de python se procesa para cada solicitud, el estado del retiro, de acuerdo con los requerimientos del enunciado, las reglas definidas, el glosario de razones y las aclaraciones dadas, se crean 2 nuevos archivos de excel; decisions_db.xlsx, donde se encuentran 4 hojas, la hoja Decisions_db presenta todas las decisiones, la hoja Rejects, solo las rechazadas, la hoja Approvals, solo las aceptadas y en la hoja Dashboard, un resumen de la cantidad approve, hold y reject, al igual que las cantidades las solicitudes de acuerdo a su reason_code. El otro archivo que se genera es 'Review_queue.xlsx', en el cual estan todos los HOLDS ordenados por Severity de mayor a menor.

    BONO: Se creo un agente con el objetivo de automatizar este proceso, facilitar la toma de decisiones y realizar procesos mas eficientes. El agente sigue este flujo:
```
CAPA 1 — Ingesta
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│ withdrawals.xlsx│────▶│   Data loader    │────▶│  Cola de solicitudes │
│  o webhook/API  │     │ pandas+openpyxl  │     │    Redis / SQS       │
└─────────────────┘     └──────────────────┘     └──────────────────────┘

CAPA 2 — Motor de reglas
                    ┌──────────────────────────────────────┐
                    │         Motor de reglas (Python)     │
                    │   REJECT / HOLD / APPROVE — determin │
                    └──────────────────────────────────────┘
                         │              │              │
                      REJECT          HOLD          APPROVE

CAPA 3 — Decisión inicial
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Auto-reject    │  │ HOLD enrichment  │  │  Auto-approve    │
│ Notificar cliente│  │ Envía a Claude   │  │ Ejecutar retiro  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                                │
CAPA 4 — Agente LLM             ▼
                    ┌──────────────────────────────────────┐
                    │    Agente Claude (claude-sonnet-4-6) │
                    │  Analiza contexto del cliente        │
                    │  Genera narrativa + sugiere acción   │
                    │  Score de prioridad y resumen audit  │
                    └──────────────────────────────────────┘
                                │
CAPA 5 — Outputs                ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   decisions_db   │  │  review_queue    │  │   audit_log      │
│ PostgreSQL/Excel │  │ HOLDs+narrativa  │  │  Trazabilidad    │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                                │
CAPA 6 — Revisión humana        ▼
                    ┌──────────────────────────────────────┐
                    │      Panel de revisión humana        │
                    │  Retool/Streamlit — 1 clic APPROVE   │
                    │  Slack alert si severity ≥ 90        │
                    └──────────────────────────────────────┘
                                │
                    ◀───────────┘  feedback loop
```

    El archivo 'withdrawal_agent' recibe el archivo de excel, luego de esto, con el codigo de python que habiamos usado anteriormente procesa las solicitudes como ya lo habia hecho de acuerdo a si es REJECT, APPROVE o HOLD. Para el apoyo de decisones se integra la API de anthropic la cual analiza las solicitudes HOLD, analizando el contexto del cliente, y sugiriendo una accion respectiva. Con el uso del agente se generan los archivos anteriores decisions_db.xlsx, review_agent_queue.xlsx, con las recomendaciones de la LLM para una mejor toma de decisiones y un nuevo archivo audit_log.json con el fin de llevar la trazabilidad completa de cada decisiones para compliance.

    Para ejecutar el agente, siga los siguientes pasos: 
        1. Instale las librerias requeridas: pip install anthropic pandas openpyxl
        2. Configure la API Key de Anthropic (yo la proveo en caso de que no la tenga):export ANTHROPIC_API_KEY="sk-ant-api03-TU-KEY-AQUI"
        3. Es necesario tener el archivo withdrawals.xlsx en la misma carpeta
        4. En su terminal ejecute: python withdrawal_agent.py
        5. El agente empezara su funcionamiento y generara los archivos definidos anteriormente con ayuda de la LLM.
    
    En caso de que se desee aprobar y rechazar HOLDS manualmente: 
        1. En su terminal ejecute: python withdrawal_agent.py --interactive
        Con esto podra hacerlo 

    Mejoras al modelo actual: Si todo se maneja localmente, como lo es actualmente en un archivo de excel, se puede definir un 'watcher', que se quede pendiente de si se modifica el archivo withdrawals.xlsx, cuando detecte un cambio (que se añada nueva informacion u otra solicitud), se ejecuta el agente (withdrawal_agent.py) y este regenera los archvos, estando en todo momento actualizados.

    Mejoras en otro modelo:
        Se puede implementar una automatizacion que siga los mismos paramentros, herramientas que son mas faciles de usar como MAKE o N8N, permiten recibir por parametros hojas de excel con webhooks instantaneos para que cada vez que alguien incluya informacion se activen, siguiendo la misma logica del LLM, y genere los archivos. Este metodo es mas facil de implementar (NO CODE) pero genera cobro por creditos dado su uso, que incluyendo el pago de la API de anthropic, hace necesario analizar los costos de implementacion, pero promueve un funcionamiento escalable y eficiente sin requerir intervencion humana.

4. Solucion con Agente: 

    4.1.1 ¿Cómo funciona ACH en EE.UU.?

    Por sus siglas ACH es Automated Clearing House, sirve para procesar transferencias en Estados Unidos, y funciona en los lotes. 
    Empieza por el Originator (cliente) que es el que autoriza que se le debite dinero de su cuenta, luego pasa al OFDI que es el procesador de pagos, el cual agrupa las ordenes y las manda al ACH Network, que es la infraestructura de la reserva federal que se encarga de llevar el dinero al banco que es, o sea al RDFI que es el banco que la recibe y finalmente, le da o quita la plata al Receiver.
    En una ACH estandar, el dinero liquida el dia habil siguiente, pero para los fondos esten disponibles tarda entre 3 a 5 dias en la cuenta de la inversion.
    En un Same-Day ACH, si la orden se envia antes de la 1pm, los fondos se liquidan ese mismo dia. 

    Para un cliente Insight, recomendaria Same-Day, cuando necesite los fondos disponibles con urgencia o cuando quiera aprovechar una oportunidad de inversion el mercado. 

    4.1.2 Requisitos para fondear una cuenta de inversión vía ACH

    Para fondear via ACH, el cliente necesita tener: su nombre legal completo tal como aparece en el banco, el nombre del banco, el routing number ABA, el número de cuenta, y el tipo de cuenta (corriente o de ahorros).

    Cuando el cliente registra su cuenta, Insights envía dos micro-depósitos menores a $1 para verificar que la cuenta es real y pertenece al cliente. Esos depósitos aparecen en el extracto bancario en 1 o 2 días hábiles, y el cliente debe confirmar los montos exactos en la plataforma antes de poder fondear.

    Los límites son $50 como mínimo y $250,000 como max por transacción. Los fondos quedan disponibles entre 3 y 5 días hábiles para ACH estándar, o el mismo día si se usa Same-Day ACH antes de la 1 PM ET.

    En cuanto a rechazos, los tres más frecuentes son:
    R01 — Fondos insuficientes: El saldo disponible era menor al monto solicitado al momento del procesamiento. El mensaje al cliente sería: "Tu banco rechazó la transferencia por fondos insuficientes. Por favor verifica tu saldo y vuelve a intentarlo con un monto menor o espera a que tu próximo depósito esté disponible. No se generó ningún cargo en tu cuenta Insights."

    R03 — Cuenta no encontrada: El routing o número de cuenta no corresponde a ninguna cuenta activa. El mensaje: "No pudimos localizar tu cuenta bancaria. Por favor verifica que el routing number y número de cuenta sean correctos y vuelve a intentarlo. Si el problema persiste, contáctanos en support@insightsinvest.com."

    R02 — Cuenta cerrada: La cuenta fue cerrada antes de que se procesara la transacción. El mensaje: "La cuenta bancaria que registraste está cerrada. Por favor agrega una cuenta activa desde Funding, luego, Add Bank Account."

    4.1.3 Routing numbers (ABA): lógica y lookup por banco y estado

    Un ABA routing number es un numero de 9 dígitos que identifica a una institución financiera (banco) dentro del sistema de pagos de EE.UU.

    Los primeros 4 dígitos identifican el distrito de la Reserva Federal y el banco dentro de ese distrito. Los siguientes 4 identifican la institución específica. Y el noveno es un dígito verificador que se calcula con una fórmula matemática para detectar errores de tipeo.

    La razón por la que un banco puede tener routing numbers distintos según el estado es porque los grandes bancos nacionales como Bank of America o Wells Fargo crecieron absorbiendo bancos regionales más pequeños a lo largo de décadas. Cada uno de esos bancos tenía su propio routing, y al fusionarse se mantuvieron para no interrumpir los pagos programados de los clientes que ya tenian. De igual manera, EE.UU. tiene 12 distritos de la Reserva Federal, y los routing numbers están atados a esos distritos geográficos.

    El banco internamente es define el nombre del banco y el estado para buscar en su tabla de referencia, y devolver el número correspondiente. Se espera que se le pida al cliente que lo confirme contra su app bancaria o el fondo de un cheque, porque los bancos pueden actualizarlos tras fusiones.

    Tabla de Routing Numbers — 10 Bancos Comunes (Enfoque Latino en EE.UU.)

| # | Banco | Estado | Routing Number | Fuente |
|---|-------|--------|----------------|--------|
| 1 | **Bank of America** | California | 121000358 | [bankofamerica.com](https://www.bankofamerica.com) |
| 1 | **Bank of America** | Texas | 026009593 | [bankofamerica.com](https://www.bankofamerica.com) |
| 1 | **Bank of America** | Florida | 063100277 | [bankofamerica.com](https://www.bankofamerica.com) |
| 2 | **Wells Fargo** | California | 121042882 | [wellsfargo.com](https://www.wellsfargo.com) |
| 2 | **Wells Fargo** | Texas | 111900659 | [wellsfargo.com](https://www.wellsfargo.com) |
| 2 | **Wells Fargo** | Florida | 063107513 | [wellsfargo.com](https://www.wellsfargo.com) |
| 3 | **Chase** | Nueva York | 021000021 | [chase.com](https://www.chase.com) |
| 3 | **Chase** | Texas | 111000614 | [chase.com](https://www.chase.com) |
| 3 | **Chase** | Florida | 267084131 | [chase.com](https://www.chase.com) |
| 4 | **Citibank** | Nueva York | 021000089 | [citibank.com](https://www.citibank.com) |
| 4 | **Citibank** | California | 322271724 | [citibank.com](https://www.citibank.com) |
| 5 | **TD Bank** | Nueva Jersey / Pennsylvania | 031101266 | [tdbank.com](https://www.tdbank.com) |
| 5 | **TD Bank** | Nueva York | 026013673 | [tdbank.com](https://www.tdbank.com) |
| 5 | **TD Bank** | Florida | 067014822 | [tdbank.com](https://www.tdbank.com) |
| 6 | **Banco Popular** | Nueva York | 021502011 | [bancopopular.com](https://www.bancopopular.com) |
| 6 | **Banco Popular** | Florida | 067010898 | [bancopopular.com](https://www.bancopopular.com) |
| 6 | **Banco Popular** | Nueva Jersey | 021202337 | [bancopopular.com](https://www.bancopopular.com) |
| 7 | **BBVA USA** | Texas | 113010547 | [bbvausa.com](https://www.bbvausa.com) |
| 7 | **BBVA USA** | California | 122238420 | [bbvausa.com](https://www.bbvausa.com) |
| 7 | **BBVA USA** | Alabama | 062001186 | [bbvausa.com](https://www.bbvausa.com) |
| 8 | **Regions Bank** | Alabama | 062000019 | [regions.com](https://www.regions.com) |
| 8 | **Regions Bank** | Florida | 063104668 | [regions.com](https://www.regions.com) |
| 8 | **Regions Bank** | Texas | 113000023 | [regions.com](https://www.regions.com) |
| 9 | **Truist** | Carolina del Norte | 053101121 | [truist.com](https://www.truist.com) |
| 9 | **Truist** | Georgia | 061000104 | [truist.com](https://www.truist.com) |
| 9 | **Truist** | Florida | 063102152 | [truist.com](https://www.truist.com) |
| 10 | **PNC Bank** | Pennsylvania | 043000096 | [pnc.com](https://www.pnc.com) |
| 10 | **PNC Bank** | Nueva Jersey | 031207607 | [pnc.com](https://www.pnc.com) |
| 10 | **PNC Bank** | Florida | 267084199 | [pnc.com](https://www.pnc.com) |

    4.1.4 Comparativa: ACH vs Wire vs Debit Card 
## 4.1.4 Comparativa: ACH vs Wire vs Debit Card

| Criterio | ACH | Wire Transfer | Debit Card |
|----------|-----|---------------|------------|
| **Velocidad** | 3–5 días hábiles (estándar) / mismo día (Same-Day ACH antes de 1 PM ET) | Mismo día si se envía antes del cut-off (~4 PM ET) | Inmediato (autorización) / 1–2 días (liquidación) |
| **Costo para el cliente** | Gratis o hasta $3 | $15–$35 doméstico / $40–$65 internacional | 0–2.5% del monto |
| **Costo para Insights** | $0.20–$0.50 por transacción | $10–$25 por transacción recibida | 1.5–3% del monto (interchange) |
| **Límites típicos** | $50 mín / $250,000 máx por transacción | Sin límite práctico | $10,000 por transacción (límite VISA/MC) |
| **Reversibilidad** | ✅ Sí — hasta 60 días para débitos no autorizados | ❌ No — irreversible una vez enviado | ✅ Sí — chargeback en 60–120 días |
| **Seguridad** | Requiere autorización previa del cliente | Alto riesgo si hay wire fraud | Protecciones de red VISA/Mastercard |
| **Experiencia de usuario** | Se configura una vez, después es 1 clic | Proceso manual completo cada vez | Inmediato y familiar, pero tiene comisión |
| **Disponibilidad horaria** | 24/7 para iniciar / procesa en ventanas batch | Solo días y horas hábiles bancarias | 24/7 |
| **Cobertura geográfica** | Solo dentro de EE.UU. | Nacional e internacional | Nacional e internacional |
| **Infraestructura requerida** | Procesador ACH (Plaid, Dwolla, Stripe) | Banca corresponsal | Merchant account + payment gateway |

---

    Es mejor ACH por: 

        - Es el más barato a escala — los clientes pueden hacer fondeos, y se les cobra $0.30 por ACH vs $25 por Wire.
        - Se configura una sola vez, y después se fondea con un clic, sin volver a ahcer todo el proceso.
        - Es reversible, entonces, si hay un error o fraude, se puede recuperar el dinero.

    ¿Cuándo recomendar Wire o Debit Card?

        Wire: cuando el monto supera los $250,000 o el cliente necesita que rapido.
        Debit Card: cuando el cliente no tiene cuenta bancaria en EE.UU. o quiere fondear menos de $1,000 de forma inmediata


    4.2 Diseño del agente (arquitectura y flujo conversacional)


### Propósito

> El agente Insights ACH Funding Assistant guía a clientes de la plataforma Insights
> a través del proceso completo de fondeo de cuenta vía ACH, desde la recopilación
> de datos bancarios hasta la confirmación del transfer, manejando errores y
> escalamientos de forma autónoma.

---

### Flujo Conversacional Completo
```
┌─────────────────────────────────────────────────────────┐
│                    INICIO DE SESIÓN                     │
│  Cargar historial si --session <id>                     │
│  Generar saludo automático                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 1: INTENCIÓN                                    │
│  ¿El cliente quiere fondear vía ACH?                    │
│  → ACH: continuar flujo                                 │
│  → Wire o Debit Card: explicar diferencias y redirigir  │
└──────────────────────┬──────────────────────────────────┘
                       │ ACH confirmado
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 2: RECOPILACIÓN DE DATOS                        │
│                                                         │
│  2a. ¿Cuál es tu nombre legal completo?                 │
│  2b. ¿En qué banco tienes la cuenta? ← OBLIGATORIO      │
│  2c. ¿En qué estado está registrada? ← OBLIGATORIO      │
│      ┌────────────────────────────┐                     │
│      │  TOOL: routing_lookup()    │                     │
│      │  Input:  banco + estado    │                     │
│      │  Output: ABA routing #     │                     │
│      └────────────────────────────┘                     │
│  2d. ¿Cuál es tu número de cuenta?                      │
│  2e. ¿Es checking o savings?                            │
│  2f. ¿Cuánto deseas transferir?                         │
└──────────────────────┬──────────────────────────────────┘
                       │ Todos los datos recopilados
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 3: ROUTING LOOKUP Y CONFIRMACIÓN                │
│  Mostrar routing inferido al cliente                    │
│  Pedir que lo verifique en su app bancaria              │
│  Si duda → indicar cómo verificarlo                     │
└──────────────────────┬──────────────────────────────────┘
                       │ Cliente confirma datos
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 4: INSTRUCCIONES PASO A PASO                    │
│  Step 1: Login → app.insightsinvest.com                 │
│  Step 2: Funding → Add Bank Account                     │
│  Step 3: Ingresar routing + account + tipo              │
│  Step 4: Esperar micro-depósitos (1–2 días hábiles)     │
│  Step 5: Verificar montos en la plataforma              │
│  Step 6: Fund Account → monto → confirmar               │
│  Step 7: Fondos disponibles en 3–5 días hábiles         │
└──────────────────────┬──────────────────────────────────┘
                       │ Cliente confirma comprensión
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 5: CONFIRMACIÓN Y CIERRE                        │
│  Resumen: nombre, banco, routing, monto, fecha estimada │
│  Soporte: support@insightsinvest.com                    │
│  Guardar sesión para memoria futura                     │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │ Cliente reporta error│
            └──────────┬──────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 6: MANEJO DE FALLOS                             │
│                                                         │
│  R01 → Fondos insuficientes → sugerencia de reintento   │
│  R02 → Cuenta cerrada → agregar nueva cuenta            │
│  R03 → Cuenta no encontrada → verificar datos           │
│  R07 → Autorización revocada → contactar soporte        │
│  Desconocido → Escalar a agente humano                  │
└──────────────────────┬──────────────────────────────────┘
                       │ 3+ fallos o tema legal/fraude
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ESTADO 7: ESCALAMIENTO                                 │
│  Conectar con especialista humano                       │
│  Dar: email + teléfono + session ID                     │
└─────────────────────────────────────────────────────────┘
```

---

### Matriz de Preguntas y Acciones

| # | El agente pregunta | Respuesta esperada | Acción del agente |
|---|-------------------|-------------------|-------------------|
| 1 | Intención de fondeo | "quiero fondear / ACH" | Confirmar y continuar |
| 2a | Nombre legal completo | "María García" | Guardar en contexto |
| 2b | **Banco (OBLIGATORIO)** | "Bank of America" | Guardar; esperar estado |
| 2c | **Estado (OBLIGATORIO)** | "Texas" | Llamar routing_lookup() |
| — | [TOOL] routing_lookup | — | Mostrar ABA routing number |
| 2d | Número de cuenta | "4567891234" | Registrar número |
| 2e | Tipo de cuenta | "checking / savings" | Registrar tipo |
| 2f | Monto a transferir | "$5,000" | Validar límites ($50–$250K) |
| 3 | Confirmar datos | "sí, correcto" | Proceder a instrucciones |
| 4–5 | ¿Entendiste los pasos? | "sí / tengo dudas" | Clarificar o cerrar sesión |

---

### Estados y Transiciones
```
INICIO → INTENCIÓN → RECOPILACIÓN → ROUTING_LOOKUP
                                          │
                          ┌───────────────┘
                          ▼
                    INSTRUCCIONES → CONFIRMACIÓN → CERRADO
                          │
                          └→ MANEJO_FALLOS → ESCALAMIENTO
```

**Reglas de transición:**
- El agente **nunca avanza al Estado 3** sin tener banco + estado confirmados
- Un fallo R01 o R03 **no termina la sesión** — el agente intenta resolver primero
- Solo escala si hay **3 o más fallos consecutivos** o el cliente menciona fraude o temas legales
- El historial de conversación se guarda en disco para poder **retomar la sesión** con `--session <id>`

---

### Arquitectura Técnica
```
┌─────────────────────────────────────┐
│         CLI / Telegram              │
│     (entrada y salida de texto)     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│           agent.py                  │
│  - Loop conversacional              │
│  - Gestión de sesiones (JSON)       │
│  - Tabla de routing simulada        │
└────────────────┬────────────────────┘
                 │ HTTPS
                 ▼
┌─────────────────────────────────────┐
│     Anthropic Claude (API)          │
│  - System prompt con flujo          │
│  - Tool: routing_lookup()           │
│  - Manejo de R-codes                │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      sessions/<id>.json             │
│  - Historial de conversación        │
│  - Reutilizable con --session <id>  │
└─────────────────────────────────────┘
```

    4.3 System prompt (el “cerebro” del agente)

        You are Insights ACH Funding Assistant — a friendly, professional agent for Insights Investment Platform.
        Your sole purpose is to help customers fund their Insights investment account via ACH bank transfer.

        === TONE & PERSONA ===
        - Warm, clear, concise. Never robotic or overly formal.
        - Address the customer by name once you know it; otherwise use "you."
        - Never invent information. If unsure, say so and escalate.
        - Respond in the same language the user writes in (English or Spanish supported).

        === MANDATORY FIRST STEPS (do NOT skip) ===
        Before providing any routing number, ACH instructions, or funding guidance:
        1. Ask for the customer's BANK NAME.
        2. Ask for the STATE where that bank account is registered.
        Only after you have BOTH pieces of information should you call the routing_lookup tool.

        === CONVERSATION FLOW ===

        STATE 1 — GREETING & INTENT CONFIRM
        - Greet warmly, introduce yourself.
        - Confirm the customer wants to fund via ACH.

        STATE 2 — DATA COLLECTION (in this order, one at a time)
        a. Full legal name (as it appears on bank account)
        b. Bank name
        c. State where bank account is held
        → Call routing_lookup tool after receiving bank + state.
        d. Bank account number
        e. Account type (checking / savings)
        f. Funding amount (USD)

        STATE 3 — ROUTING LOOKUP & CONFIRMATION
        - Present routing number from tool.
        - Ask customer to verify with their bank app or checkbook if unsure.

        STATE 4 — STEP-BY-STEP FUNDING INSTRUCTIONS
        Step 1: Log in at app.insightsinvest.com
        Step 2: Go to Funding > Add Bank Account
        Step 3: Enter bank name, routing number, account number, account type
        Step 4: Insights sends 2 micro-deposits (< $1 each) within 1-2 business days
        Step 5: Return to Funding > Verify Account, enter both micro-deposit amounts
        Step 6: Go to Fund Account, enter amount, confirm
        Step 7: Funds available in 3-5 business days (Standard ACH) or same day if Same-Day ACH eligible (submit before 1 PM ET)

        STATE 5 — CONFIRMATION & WRAP-UP
        - Summarize: name, bank, routing, amount, expected availability.
        - Support: support@insightsinvest.com | 1-800-INSIGHTS

        STATE 6 — FAILURE HANDLING
        When customer mentions a failed transfer, match to these codes:

        R01 - Insufficient Funds:
            Say: "Your bank returned code R01 — Insufficient Funds. Your account balance was lower than the transfer amount. Please check your balance and retry with a smaller amount or wait for your next deposit. No fee has been charged to your Insights account."

        R03 - No Account / Unable to Locate:
            Say: "Your bank returned code R03 — Account Not Found. This typically means the account number or routing number was entered incorrectly, or the account has been closed. Please verify both numbers with your bank and re-initiate the transfer. If the problem persists, contact support@insightsinvest.com."

        R02 - Account Closed:
            Say: "Code R02 — Account Closed. Please add a new active bank account under Funding > Add Bank Account."

        R07 - Authorization Revoked:
            Say: "Code R07 — Authorization Revoked. Please contact us at support@insightsinvest.com to re-authorize the transfer."

        Generic failure:
            Acknowledge, summarize, escalate to support@insightsinvest.com | 1-800-INSIGHTS, reference session ID [SESSION_ID].

        === ESCALATION ===
        Escalate immediately if: customer frustrated 3+ times, legal/compliance questions, fraud mentioned.
        → "I'm connecting you with a senior support specialist: support@insightsinvest.com | 1-800-INSIGHTS"

        === KNOWLEDGE ===
        - Standard ACH: 3-5 business days for funds to be available
        - Same-Day ACH: submit before 1 PM ET, available same day, max $1,000,000
        - Limits: $50 min, $250,000 max per transaction at Insights
        - ACH is reversible within ~60 days for unauthorized debits
        - Micro-deposit verification required on first linked account

        === DISCLAIMER ===
        Routing numbers are based on published data; always verify with your bank. Insights does not provide tax or legal advice.

    4.4 Implementación (prototipo funcional)

    Se desarrollo dos agentes, uno en la consola y otro en telegram, descargue toda la carpeta AGENTE-WM, a continuacion los pasos para su debida ejecucion: 

    BONUS: Se realizaron los agentes con memoria entre sesiones para recordar banco/estado y no preguntarlo de nuevo.

    TERMINAL:
        Para implemetar el agente, siga los siguientes pasos: 

            1. Ingrese la API Key de Anthropic en la terminal (si no la tiene, me la pide y yo la proveo): export ANTHROPIC_API_KEY="sk-ant-api03-TU-KEY-AQUI"
            2. Corra el agente en la terminal: python agent.py
            3. Puede ya probar el agente 

    Telegram: 
        Para implemetar el agente, siga los siguientes pasos: 
        1. Ingrese la API de telegrama: export TELEGRAM_BOT_TOKEN="8759702543:AAHxzIBVQax6ICka8RMu2GtUwJ5GGHNhrsg"
        Ese es el API de telegram real que debe ingresar en su terminal, luego de descargar la carpeta.
        2. Ingrese la API Key de Anthropic en la terminal (si no la tiene, me la pide y yo la proveo): export ANTHROPIC_API_KEY="sk-ant-api03-TU-KEY-AQUI"
        3. Corra el agente en la terminal: python telegram_bot.py
        4. En el telegram busque InsightsACHbot
        5. Abra el chat con el bot y escriba "/start", ya puede conversar con el bot 


    4.5 Demo y reflexion 

    En la carpeta AGENTE-WM, puede encontrar 3 escenarios de la transcripcion: 

        demo_escenario1.txt: exito 
        demo_escenario2.txt: R01
        demo_escenario1.txt: R03

    Tambien tiene un link de YouTube, con el chatbot de telegram para tambien ver su correcto funcionamiento: https://youtu.be/7LkPVGCboxU?si=_njUDiLJk_41Hjvs

    Tambien se realizo una ejecucion del agente, en una pagina web (similar a INSIGHTS WM), para atender a los clientes unicamente sobre sus depositos ACH, aqui se puede ejecutar un agente de voz en la esquina inferior derecha y este le ayuda a sus transaccion ACH, el link de la pagina web es: https://insights-ai-landing.lovable.app

    Reflexion: 
    Construir este agente me permitió entender en la práctica la diferencia entre
    un chatbot que responde preguntas y un agente que guía un proceso con lógica
    de negocio real. Lo chevere del ejercicio fue diseñar el flujo de estados:
    obligar al agente a preguntar banco y estado antes de dar cualquier dato no es
    solo una regla arbitraria, es la diferencia entre un routing correcto y un R03.

    Con más tiempo, lo primero que mejoraría es reemplazar la tabla de routing
    estática por una integración real con Plaid o la API del ABA. Los routing
    numbers cambian cuando los bancos se fusionan, y una tabla hardcodeada tiene
    fecha de expiración. También añadiría validación del dígito verificador del
    routing antes de enviarlo al procesador, para atrapar
    errores de tipeo antes de que generen un R03.

    La limitación más importante que encontré usando un LLM para manejar fallos
    ACH es que el modelo tiende a ser demasiado creativo con los mensajes de error.
    En un contexto financiero regulado, el texto exacto de una respuesta a un R01
    o R03 tiene implicaciones legales y de compliance  no puede variar según el
    humor del modelo. La solución correcta es usar el LLM solo para el diálogo
    natural y templates predefinidos para los mensajes regulatorios, sin dejar
    que el modelo los genere libremente. Esa separación entre "conversación libre"
    y "mensajes de cumplimiento" es algo que implementaría desde el diseño inicial.
