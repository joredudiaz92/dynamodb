import boto3
import uuid
import random
from datetime import datetime, timedelta

def bulk_insert_custom_mock_data():
    db_resource = boto3.resource(
        'dynamodb',
        region_name='us-east-1')
    
    # Instanciar las referencias a las tablas
    t_clients = db_resource.Table('clients')
    t_cards = db_resource.Table('cards')
    t_transactions = db_resource.Table('transactions')

    base_time = datetime(2026, 8, 17, 14, 30, 0)

    print("🚀 Iniciando generación y carga masiva optimizada...")

    # ==========================================
    # 1. GENERAR DOCUMENT_TYPES (Exactamente 5 registros)
    # ==========================================
    print("⏳ Seteandp exactamente 5 tipos de documentos...")
    doc_types_pool = ["CC", "CE", "TI", "PP", "NIT"]

    # ==========================================
    # 2. GENERAR USERS (Exactamente 2,000 registros)
    # ==========================================
    print("⏳ Creando 2,000 nombre de usuarios para funcionarios...")
    NUM_USERS = 2000
    usernames_pool = []
    
    for i in range(NUM_USERS):
        username = f"funcionario.{i:04d}"
        usernames_pool.append(username)

    # ==========================================
    # 3. GENERAR CLIENTS (Exactamente 15,000 registros)
    # ==========================================
    print("⏳ Insertando 15,000 clientes relacionales...")
    NUM_CLIENTS = 15000
    client_keys = []
    
    with t_clients.batch_writer() as batch:
        for i in range(NUM_CLIENTS):
            doc_num = f"{1110000000 + i}"
            doc_type = random.choice(doc_types_pool)
            client_keys.append((doc_num, doc_type))
            
            batch.put_item(Item={
                "document_number": doc_num,
                "document_type": doc_type,
                "name": f"ClienteName_{i}",
                "last_name": f"ClienteLastName_{i}",
                "gender": random.choice(["M", "F"]),
                "phone_number": f"318{random.randint(1000000, 9999999)}",
                "discount_type": random.choice(["Subsidio", "Transmipass", "Ninguno"]),
                "created_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "created_user": random.choice(usernames_pool), # Relacionado a los 2,000 creados
                "updated_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "updated_user": "jose_palma"
            })

    # ==========================================
    # 4. GENERAR CARDS (Exactamente 15,000 registros)
    # ==========================================
    print("⏳ Insertando 15,000 tarjetas...")
    NUM_CARDS = 15000
    card_numbers_pool = []
    
    with t_cards.batch_writer() as batch:
        for i in range(NUM_CARDS):
            card_num = f"1010{random.randint(10000,99999)}{random.randint(10000,99999)}{i:04d}"
            card_numbers_pool.append(card_num)
            
            # Cada tarjeta se vincula exactamente con uno de los 15,000 clientes
            linked_client = client_keys[i]
            ttl_epoch = 1881673800 + (i * 10)

            if random.choice(["WHITE", "BLACK"]) == "WHITE":
                batch.put_item(Item={
                    "card_number": card_num,
                    "document_number": linked_client[0], # PK del cliente para búsquedas en GSI
                    "type": "WHITE",
                    "card_status": "ACTIVE",
                    "balance_cents": random.randint(0, 500000),
                    "created_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "created_user": random.choice(usernames_pool), # Relacionado a los 2,000 creados
                    "updated_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_user": "jose_palma",
                    "ttl": ttl_epoch,
                    "version": 1
                })
            else:
                batch.put_item(Item={
                    "card_number": card_num,
                    "document_number": linked_client[0], # PK del cliente para búsquedas en GSI
                    "type": "BLACK",
                    "card_status": random.choice(["INACTIVE", "BLOCK"]),
                    "balance_cents": random.randint(0, 500000),
                    "reason_blocking": random.choice(["ROBO", "FRAUDE", "RETIRO_BENEFICIO", "NINGUNA"]),
                    "created_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "created_user": random.choice(usernames_pool), # Relacionado a los 2,000 creados
                    "updated_at": base_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "updated_user": "jose_palma",
                    "ttl": ttl_epoch,
                    "version": 1
                })

    # ==========================================
    # 5. GENERAR TRANSACTIONS (Exactamente 30,000 registros)
    # ==========================================
    print("⏳ Insertando 30,000 transacciones con integridad de negocio...")
    NUM_TRANSACTIONS = 30000
    
    with t_transactions.batch_writer() as batch:
        for i in range(NUM_TRANSACTIONS):
            tx_id = str(uuid.uuid4())
            
            # Usamos el operador módulo (%) para asegurar que las 30,000 transacciones
            # se distribuyan equitativamente entre las 15,000 tarjetas creadas.
            linked_card = card_numbers_pool[i % NUM_CARDS]
            
            batch.put_item(Item={
                "ID": tx_id,
                "card_number": linked_card,
                "type": random.choice(["ADD", "DISCOUNT"]),
                "amount": random.randint(1000, 100000),
                "created_at": (base_time + timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "created_user": random.choice(usernames_pool) # Relacionado a los 2,000 creados
            })

    print("\n✅ Base de datos poblada exitosamente con las cuotas requeridas:")
    print("   - 5 Document Types")
    print("   - 2,000 Users")
    print("   - 15,000 Clients")
    print("   - 15,000 Cards")
    print("   - 30,000 Transactions")

if __name__ == "__main__":
    bulk_insert_custom_mock_data()
