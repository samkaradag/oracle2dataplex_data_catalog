import yaml
import os
import json
from google.cloud import datacatalog_v1
from google.cloud import kms_v1
from google.cloud import secretmanager_v1
from google.api_core.client_options import ClientOptions
from google.cloud.datacatalog_v1 import Entry, Tag, TagField
import oracledb
import logging


def read_config(config_file):
  """Reads the YAML configuration file."""
  with open(config_file, 'r') as f:
    config = yaml.safe_load(f)
  return config

def get_secret(project_id, secret_id, version_id="latest"):
    """Retrieves the secret value from Secret Manager."""
    client = secretmanager_v1.SecretManagerServiceClient()
    # Build the secret name
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("utf-8")

def decrypt_password(kms_client, crypto_key_name):
  """Decrypts the password from KMS."""
  crypto_key_path = kms_client.crypto_key_path_name(
      kms_client.project,
      kms_client.location,
      kms_client.key_ring,
      crypto_key_name
  )
  response = kms_client.decrypt(name=crypto_key_path, ciphertext=os.environ.get('ORACLE_PASSWORD'))
  return response.plaintext.decode("utf-8")

def get_schemas_for_database(database_name):
    """
    Extracts a comma-separated list of schema names for a given database from a YAML .

    Args:
        database_name (str): The name of the database to search for.

    Returns:
        str: A comma-separated list of schema names, or None if the database is not found.
    """
    data = read_config("table_mapping.yaml")  # Load YAML string into a Python dictionary
    schemas = []

    for db in data.get("databases", []):
        if db["database_name"] == database_name:
            for schema in db.get("schemas", []):
                schemas.append("'" + schema["schema_name"] + "'")  

    return ",".join(schemas) if schemas else None

def get_oracle_comments(db_config):
    """Extracts column comments from the Oracle database."""
    oracle_host = db_config['host']
    service_name = db_config['service_name']
    port = db_config['port'] 
    cs = f'{oracle_host}:{port}/{service_name}'
    if db_config.get('password_kms_key'):
    #   password = decrypt_password(kms_client, db_config['password_kms_key'])
        # Retrieve password from Secret Manager
        password = get_secret(db_config["project_id"], db_config["password_secret_id"])
    else:
      password = db_config['password']
    print("Discovering column comments: ", db_config['database'])
    # connection_string = f"oracle+cx_oracle://{db_config['user']}:{password}@{db_config['host']}:{db_config['port']}/{db_config['service_name']}"
    schemas = get_schemas_for_database(db_config['database'])
    if (schemas is None):
       print("No schema found in table mappings")
       return
    else:
       print(db_config['database'], "- Schemas in mapping file: ", schemas)
    
    column_comments = {}

    with oracledb.connect(user=db_config['user'], password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT owner, table_name, column_name, comments FROM dba_col_comments WHERE OWNER IN {schemas} AND COMMENTS IS NOT NULL")
            for row in cursor:
                column_comment = {}
                print(row)
                column_comment["db_name"] = db_config['database']
                column_comment["schema_name"] = row[0]
                column_comment["table_name"] = row[1]
                column_comment["column_name"] = row[2]
                column_comment["comment"] = row[3]

                table_name = row[1] 
                try:
                    # Append to existing table's column list
                    column_comments[table_name].append(column_comment)
                except KeyError:
                    # If the table name isn't in the dictionary yet, create a new entry with a list
                    column_comments[table_name] = [column_comment]
                # column_comments[row[1]] = {row[2]:column_comment}
    return column_comments

def create_tag(field_id, project_id, location, dataset_id, table_id, column_name, tag_template_id, field_value):
    # Initialize the Data Catalog client
    # client = datacatalog_v1.DataCatalogClient()

    # Construct the fully qualified BigQuery column name
    # resource_name = f"//bigquery.googleapis.com/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
    # Lookup Data Catalog's Entry referring to the table.
    resource_name = (
        f"//bigquery.googleapis.com/projects/{project_id}"
        f"/datasets/{dataset_id}/tables/{table_id}"
    )
    table_entry = datacatalog_client.lookup_entry(
        request={"linked_resource": resource_name}
    )

    # Define the tag template name
    tag_template_name = datacatalog_client.tag_template_path(project_id, location, tag_template_id)
   
    # Create the tag
    tag = datacatalog_v1.Tag(
        template=tag_template_name,
        column=column_name,
        name=field_value,
        fields={
            field_id: datacatalog_v1.TagField(
                string_value=field_value
            )
        }
    )

    # Attach the tag to the BigQuery column
    response = datacatalog_client.create_tag(parent=table_entry.name, tag=tag)
    print(f"Created tag: {response.name}")
  
if __name__ == "__main__":
  config = read_config("config.yaml")
  
  # Initialize Data Catalog client
  datacatalog_client = datacatalog_v1.DataCatalogClient(
      client_options=ClientOptions(api_endpoint=config["datacatalog_endpoint"])
  )

  # Initialize KMS client
  kms_client = kms_v1.KeyManagementServiceClient()

  # Iterate through tables in the mapping file
  with open(config["table_mapping_file"], 'r') as f:
    table_mapping = read_config("table_mapping.yaml")  # Load YAML string into a Python dictionary

  # Iterate through database connections in config
  for db_config in config["database_connections"]:
    column_comments = get_oracle_comments(db_config)
    for db in table_mapping.get("databases", []):
        if db["database_name"] == db_config["database"]:
            for schema in db.get("schemas", []):
                for table in schema.get("tables", []):
                    for column in column_comments[table["table_name"]]:
                      print("Tagging:", column) 
                      create_tag("description", config["project_id"], config["location"], table["bigquery_dataset"], table["bigquery_table"], column["column_name"], config["tag_template_id"], column["comment"])