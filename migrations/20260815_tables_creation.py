import boto3
from botocore.exceptions import ClientError

# Inicializar cliente de DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1')

def create_tables():
    tables = [
        {
            "TableName": "cards",
            "KeySchema": [
                {"AttributeName": "card_number", "KeyType": "HASH"}
            ],
            "AttributeDefinitions": [
                {"AttributeName": "card_number", "AttributeType": "S"},
                {"AttributeName": "document_number", "AttributeType": "S"},
                {"AttributeName": "card_status", "AttributeType": "S"},
                {"AttributeName": "updated_at", "AttributeType": "S"}
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "document_number-index",
                    "KeySchema": [
                        {"AttributeName": "document_number", "KeyType": "HASH"}
                    ],
                    "Projection": {
                        "ProjectionType": "KEYS_ONLY" 
                    }
                },
                {
                    "IndexName": "card_status-updated_at-index",
                    "KeySchema": [
                        {"AttributeName": "card_status", "KeyType": "HASH"},
                        {"AttributeName": "updated_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {
                        "ProjectionType": "KEYS_ONLY"
                    }
                }
            ],
            "BillingMode": "PAY_PER_REQUEST"
        },
        {
            "TableName": "clients",
            "KeySchema": [
                {"AttributeName": "document_number", "KeyType": "HASH"},
                {"AttributeName": "document_type", "KeyType": "RANGE"}
            ],
            "AttributeDefinitions": [
                {"AttributeName": "document_number", "AttributeType": "S"},
                {"AttributeName": "document_type", "AttributeType": "S"}
            ],
            "BillingMode": "PAY_PER_REQUEST"
        },
        {
            "TableName": "transactions",
            "KeySchema": [
                {"AttributeName": "ID", "KeyType": "HASH"} # PK Principal única
            ],
            "AttributeDefinitions": [
                {"AttributeName": "ID", "AttributeType": "S"},
                {"AttributeName": "card_number", "AttributeType": "S"}, # Necesario por ser PK del GSI
                {"AttributeName": "created_at", "AttributeType": "S"}   # Necesario por ser SK del GSI
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "card_number-created_at-index",
                    "KeySchema": [
                        {"AttributeName": "card_number", "KeyType": "HASH"}, # FK mapeada
                        {"AttributeName": "created_at", "KeyType": "RANGE"}  # SORT KEY para ordenar por tiempo
                    ],
                    "Projection": {
                        "ProjectionType": "KEYS_ONLY" # Proyecta todos los campos en las consultas del GSI
                    }
                }
            ],
            "BillingMode": "PAY_PER_REQUEST"
        }      
    ]

    for table in tables:
        try:
            dynamodb.create_table(**table)
            print(f"✅ Tabla '{table['TableName']}' creada.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️ Tabla '{table['TableName']}' ya existe.")

if __name__ == "__main__":
    create_tables()
    # Esperar unos segundos a que AWS active las tablas antes de insertar puede ser necesario en producción
    import time; time.sleep(3) 
