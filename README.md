
# Oracle Comments to Google Data Catalog Connector

This tool helps you automatically extract comments from your Oracle database and tag them as descriptions in Google Data Catalog for BigQuery tables. 

## Create Tag Templates and enable Services via Terraform
    ```bash 
        terraform init
        gcloud auth application-default login
        terraform plan -var-file terraform.tfvars 
        terraform apply -var-file terraform.tfvars 


# Oracle Database User
## Priviledges needed 
GRANT SELECT ON DBA_COL_COMMENTS TO catalog_reader; 
this needs to be granted by sys user.

Sample query:
SELECT owner, table_name, column_name, comments FROM dba_col_comments;

## Use service acccount or gcloud auth application-default login with your oauth credentials
export GOOGLE_APPLICATION_CREDENTIALS=~/credentials/datacatalog-tag-template-processor-sa.json



## Features

* **Direct Oracle Connection:** Connects directly to your Oracle database to fetch column comments.
* **Flexible Configuration:** Supports various ways to store and retrieve your Oracle credentials:
    * Plaintext password in config file (for testing or local development)
    * Google Secret Manager to securely store your password
    * KMS to encrypt and decrypt your password 
* **Table Mapping:**  Defines the mapping between Oracle schemas and tables to their corresponding BigQuery datasets and tables. 
* **Data Catalog Tagging:** Creates tags in Google Data Catalog with the column comments as descriptions.
* **Containerized:** Can be run in any Linux-based machine or containerized environment.

## Prerequisites

* **Google Cloud Project:**  A Google Cloud project with the Data Catalog and KMS APIs enabled.
* **Google Cloud CLI:**  Installed and configured.
* **Oracle Database:** An Oracle database accessible with appropriate permissions.
* **Python 3.7 or higher:**  Installed on your machine. 
* **Python Libraries:** Install the required Python libraries:
   ```bash
   pip install requirements.txt
   python oracle-extractor-tagger.py 