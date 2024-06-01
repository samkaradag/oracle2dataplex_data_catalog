terraform init
gcloud auth application-default login
terraform plan -var-file terraform.tfvars 
terraform apply -var-file terraform.tfvars 

# oracle2dataplex_data_catalog
This tool extracts Oracle Metadata such as Column Comments, gets a mapping table listing Oracle source tables to BigQuery tables, and populates Dataplex / Data Catalog with column aspects/tags


# Oracle Database User
needs 
GRANT SELECT ON DBA_COL_COMMENTS TO catalog_reader; 
<!-- GRANT SELECT ON DBA_TAB_COLUMNS TO catalog_reader; 
GRANT SELECT ON DBA_TAB_COLS TO catalog_reader; 
GRANT SELECT ON DBA_TABLES TO catalog_reader;  -->
this needs to be granted by sys user.

SELECT owner, table_name, column_name, comments FROM dba_col_comments WHERE OWNER IN 'MOCKSCHEMA';

export GOOGLE_APPLICATION_CREDENTIALS=~/credentials/datacatalog-tag-template-processor-sa.json
