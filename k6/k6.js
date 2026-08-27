import { check, sleep } from 'k6';
import http from 'k6/http';
import { Trend, Counter } from 'k6/metrics';

// 1. Configuración de Métricas Personalizadas (SLIs)
const writingTrend = new Trend('dynamo_writing_duration', true);
const readingTrend = new Trend('dynamo_reading_duration', true);
const errorsCounter = new Counter('dynamo_errors_count');

// 2. Configuración de Escenarios de Carga (Total: 5 minutos / 300s)
export const options = {
    scenarios: {
        lifecycle_stress_test: {
            executor: 'ramping-vus',
            startVUs: 1,
            stages: [
                { duration: '45s', target: 5 },   // 1. Carga Baja (Warm-up)
                { duration: '1m', target: 25 },   // 2. Carga Moderada (Ramp-up)
                { duration: '2m', target: 50 },   // 3. Carga Sostenida (Plateau)
                { duration: '45s', target: 150 }, // 4. Picos de Carga (Spike)
                { duration: '30s', target: 0 },   // 5. Ramp-down (Cool-down)
            ],
            gracefulRampDown: '10s',
        },
    },
    // Umbrales de Calidad (SLOs / SLAs) sobre los SLIs resultantes
    thresholds: {
        http_req_failed: ['rate<0.01'],             // Menos del 1% de errores HTTP globales
        dynamo_errors_count: ['count<50'],          // Máximo 50 errores de lógica Dynamo
        'dynamo_reading_duration': ['p(95)<30'],    // El 95% de las lecturas locales deben ser < 30ms
        'dynamo_writing_duration': ['p(95)<45'],    // El 95% de las escrituras locales deben ser < 45ms
    },
};

const DYNAMO_URL = 'http://localhost:8000';
const BASE_HEADERS = {
    'Content-Type': 'application/x-amz-json-1.0',
};

// Pools de datos alineados con tu script de Python para simular colisiones y lecturas reales
const docTypesPool = ["CC", "CE", "TI", "PP", "NIT"];

export default function () {
    // Generadores de IDs pseudo-aleatorios basados en los límites de tu semilla
    const randomUserIdx = Math.floor(Math.random() * 2000);
    const randomClientIdx = Math.floor(Math.random() * 15000);
    const randomCardIdx = Math.floor(Math.random() * 15000);

    const targetUsername = `funcionario.${String(randomUserIdx).padStart(4, '0')}`;
    const targetDocNum = String(1110000000 + randomClientIdx);
    const targetDocType = docTypesPool[Math.floor(Math.random() * docTypesPool.length)];

    // Decisión de flujo: 60% Lecturas (Reads) y 40% Escrituras (Writes)
    const isReadOperation = Math.random() < 0.60;

    if (isReadOperation) {
        // ==========================================
        // FLUJO DE LECTURA (GetItem)
        // ==========================================
        // Alternamos lecturas de manera aleatoria entre Clientes, Usuarios y Tarjetas
        const tableSelector = Math.random();
        let payload = '';
        let targetOp = 'DynamoDB_20120810.GetItem';
        let cardNumber = `1010 ${Math.floor(10000 + Math.random() * 90000)} ${Math.floor(10000 + Math.random() * 90000)} ${String(randomCardIdx).padStart(4, '0')}`;

        if (tableSelector < 0.4) {
            // Lectura de Cliente (Llave compuesta: Partition + Sort Key)
            payload = JSON.stringify({
                TableName: 'clients',
                Key: { 'document_number': { S: targetDocNum }, 'document_type': { S: targetDocType } }
            });
        } else {
            // Lectura de Document Types fijo (ID)
            payload = JSON.stringify({
                TableName: 'cards',
                Key: { 'card_number': { S: cardNumber } }
            });
        }

        const startTime = Date.now();
        const res = http.post(DYNAMO_URL, payload, {
            headers: Object.assign({}, BASE_HEADERS, {
                'X-Amz-Target': targetOp,
                'Content-Type': 'application/x-amz-json-1.0',
                // Headers de autenticación ficticios requeridos por el motor local:
                'Authorization': 'AWS4-HMAC-SHA256 Credential=mock/20260824/us-east-1/dynamodb/aws4_request, SignedHeaders=content-type;host;x-amz-target, Signature=mock',
                'X-Amz-Date': '20260824T200000Z'
            })
        });
        readingTrend.add(Date.now() - startTime);

        const success = check(res, { 'Read HTTP 200': (r) => r.status === 200 });
        if (!success) {
            errorsCounter.add(1);
            console.error(`🚨 Error Lectura: Status ${res.status} | Body: ${res.body}`);
        }

    } else {
        // ==========================================
        // FLUJO DE ESCRITURA (PutItem / Transactions)
        // ==========================================
        // Simulamos la creación constante de nuevas transacciones en tiempo real
        const newTxId = `tx-k6-${Math.floor(Math.random() * 10000000)}-${__VU}-${__ITER}`;
        // Formato aproximado de la máscara de tu generador de tarjetas python
        const simulatedCardNum = `1010 ${Math.floor(10000 + Math.random() * 90000)} ${Math.floor(10000 + Math.random() * 90000)} ${String(randomCardIdx).padStart(4, '0')}`;

        const payload = JSON.stringify({
            TableName: 'transactions',
            Item: {
                'ID': { S: newTxId },
                'card_number': { S: simulatedCardNum },
                'type': { S: Math.random() > 0.5 ? 'ADD' : 'DISCOUNT' },
                'amount': { N: String(Math.floor(1000 + Math.random() * 50000)) },
                'created_at': { S: new Date().toISOString() },
                'created_user': { S: targetUsername }
            }
        });

        const startTime = Date.now();
        const res = http.post(DYNAMO_URL, payload, {
            headers: Object.assign({}, BASE_HEADERS, { 
                'Content-Type': 'application/x-amz-json-1.0',
                'X-Amz-Target': 'DynamoDB_20120810.PutItem', // O la operación que ejecutes
                // Headers de autenticación ficticios requeridos por el motor local:
                'Authorization': 'AWS4-HMAC-SHA256 Credential=mock/20260824/us-east-1/dynamodb/aws4_request, SignedHeaders=content-type;host;x-amz-target, Signature=mock',
                'X-Amz-Date': '20260824T200000Z'
            })
        });
        writingTrend.add(Date.now() - startTime);

        const success = check(res, { 'Write HTTP 200': (r) => r.status === 200 });
        if (!success) {
            errorsCounter.add(1);
            console.error(`🚨 Error Escritura: Status ${res.status} | Body: ${res.body}`);
        }
    }

    // Registro periódico en consola para validar en qué etapa estamos sin saturar el output
    if (__ITER % 250 === 0) {
        console.log(`ℹ️ [VU: ${__VU}] Procesando peticiones concurrentes contra DynamoDB Local...`);
    }

    // Pacing adaptativo mínimo para evitar bloquear por completo el event loop local
    sleep(0.02); 
}

// 3. Resumen Estadístico de los SLIs al finalizar el Test
export function handleSummary(data) {
    const rTrend = data.metrics.dynamo_reading_duration.values;
    const wTrend = data.metrics.dynamo_writing_duration.values;
    const totalErrors = data.metrics.dynamo_errors_count.values.count;
    const totalReqs = data.metrics.http_reqs.values.count;

    console.log(`
===================================================================
📊 RESUMEN FINAL DE COMPORTAMIENTO Y SLIs (DYNAMODB LOCAL)
===================================================================
⏱️  Duración Total de la Prueba : 5 Minutos (Etapas de Estrés completadas)
📥  Peticiones Totales Ejecutadas: ${totalReqs}
❌  Errores Totales Detectados   : ${totalErrors}

📈  SLI: Latencias de LECTURA (GetItem)
    - Promedio (Avg) : ${rTrend.avg.toFixed(2)} ms
    - Mediana (Med)  : ${rTrend.med.toFixed(2)} ms
    - Percentil 90    : ${rTrend['p(90)'].toFixed(2)} ms
    - Percentil 95 (SLO): ${rTrend['p(95)'].toFixed(2)} ms

📉  SLI: Latencias de ESCRITURA (PutItem)
    - Promedio (Avg) : ${wTrend.avg.toFixed(2)} ms
    - Mediana (Med)  : ${wTrend.med.toFixed(2)} ms
    - Percentil 90    : ${wTrend['p(90)'].toFixed(2)} ms
    - Percentil 95 (SLO): ${wTrend['p(95)'].toFixed(2)} ms

📊  Rendimiento Global (Throughput)
    - Tasa de Éxito HTTP : ${((data.metrics.http_req_failed.values.passes / totalReqs) * 100).toFixed(4)}% fallas.
===================================================================
    `);

    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    };
}

