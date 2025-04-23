CREATE KEYSPACE IF NOT EXISTS dev_keyspace
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE dev_keyspace;

CREATE TABLE IF NOT EXISTS users (
  user_id UUID PRIMARY KEY,
  first_name text,
  last_name text,
  email text
);

DROP MATERIALIZED VIEW if exists case_data_by_value_float;
DROP MATERIALIZED VIEW if exists case_data_by_value_text;
DROP MATERIALIZED VIEW if exists case_data_by_bill_id;
DROP TABLE IF EXISTS case_data;

CREATE TABLE IF NOT EXISTS case_data (
    bill_id TEXT,
    bill_test_id TEXT,
    test_result_id TEXT,
    test_id TEXT, 
    age_in_hours INT,
    age_group TEXT,
    sex TEXT,
    cp_instance_id TEXT, 
		l_id TEXT,
		fqdn TEXT,
    parameter_id TEXT,
    parameter_name TEXT,
    parameter_printas TEXT,
    parameter_unit TEXT,
    value_float FLOAT, 
    value_text TEXT, 
    nrval_analysis TEXT, 
    help_list list<text>,
		created_at TIMESTAMP,
		updated_at TIMESTAMP,
		bill_date_quarter TEXT,
    PRIMARY KEY ((sex, parameter_printas, age_group), bill_date_quarter, cp_instance_id, test_result_id)
)	WITH CLUSTERING ORDER BY (bill_date_quarter DESC, cp_instance_id ASC, test_result_id ASC);


CREATE MATERIALIZED VIEW IF NOT EXISTS case_data_by_value_float AS
    SELECT 
			bill_id,
			bill_test_id,
			test_result_id,
			test_id, 
			age_in_hours,
			age_group,
			sex,
			cp_instance_id,
			l_id, 
			fqdn,
			parameter_id,
			parameter_name,
			parameter_printas,
			parameter_unit,
			value_float,
			value_text,
			nrval_analysis,
			help_list, 
			created_at, 
			updated_at,
			bill_date_quarter
		FROM case_data
		WHERE sex IS NOT NULL 
		AND parameter_printas IS NOT NULL
		AND age_group is NOT NULL 
		AND bill_date_quarter IS NOT NULL
		AND cp_instance_id IS NOT NULL 
		AND value_float IS NOT NULL 
		AND test_result_id IS NOT NULL
   PRIMARY KEY ((sex, parameter_printas, age_group), bill_date_quarter, value_float, cp_instance_id, test_result_id)
	 WITH CLUSTERING ORDER BY (bill_date_quarter DESC, value_float ASC, cp_instance_id ASC, test_result_id ASC);


CREATE MATERIALIZED VIEW IF NOT EXISTS case_data_by_value_text AS
    SELECT 
    	bill_id,
			bill_test_id,
			test_result_id,
			test_id, 
			age_in_hours,
			age_group,
			sex,
			cp_instance_id,
			l_id, 
			fqdn,
			parameter_id,
			parameter_name,
			parameter_printas,
			parameter_unit,
			value_float,
			value_text,
			nrval_analysis,
			help_list,
			created_at, 
			updated_at,
			bill_date_quarter
		FROM case_data
		WHERE sex IS NOT NULL 
		AND parameter_printas IS NOT NULL 
		AND age_group is NOT NULL 
		AND bill_date_quarter IS NOT NULL
		AND cp_instance_id IS NOT NULL 
		AND value_text IS NOT NULL 
		AND test_result_id IS NOT NULL
   PRIMARY KEY ((sex, parameter_printas, age_group), bill_date_quarter, value_text, cp_instance_id, test_result_id)
WITH CLUSTERING ORDER BY (bill_date_quarter DESC, value_text ASC, cp_instance_id ASC, test_result_id ASC);


CREATE MATERIALIZED VIEW IF NOT EXISTS case_data_by_bill_id AS
    SELECT 
			bill_id,
			bill_test_id,
			test_result_id,
			test_id, 
			age_in_hours,
			age_group,
			sex,
			cp_instance_id,
			l_id, 
			fqdn,
			parameter_id,
			parameter_name,
			parameter_printas,
			parameter_unit,
			value_float,
			value_text,
			nrval_analysis,
			help_list,
			created_at, 
			updated_at,
			bill_date_quarter
		FROM case_data
		WHERE bill_id IS NOT NULL 
		AND sex IS NOT NULL 
		AND parameter_printas IS NOT NULL
		AND age_group IS NOT NULL
		AND bill_date_quarter IS NOT NULL
		AND cp_instance_id IS NOT NULL
		AND test_result_id IS NOT NULL 
  PRIMARY KEY (bill_id, sex, parameter_printas, age_group, bill_date_quarter, cp_instance_id, test_result_id)
WITH CLUSTERING ORDER BY (sex ASC, parameter_printas ASC, age_group ASC, bill_date_quarter DESC, cp_instance_id ASC, test_result_id ASC);

