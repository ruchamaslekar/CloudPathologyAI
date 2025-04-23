# Data Modeling for Cloud Pathology AI

### Base Table Design

```sql
CREATE TABLE case_data (
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

```

The partition key consists of (sex, age_group, cp_instance_id, parameter_printas) because:

- These fields provide optimal data distribution:
  - sex: values ('F', 'M')
  - parameter_printas: large cardinality
  - age_group: Limited cardinality (<10 groups)
    > With 2 x 800 x 10, this yields around 16,000 partitions, which is suitable for partitioning.

bill_date_quarter, cp_instance_id, test_result_id serves as the clustering key to:

- bill_date_quarter with descending order help to query the recent medical reports
- Order data by cp_instance_id, enabling efficient lookups for specific cp_instance_id values
- Ensure row uniqueness within each partition
- Provide natural ordering of test results

### Value-based Analysis View

```sql
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
		AND age_group is NOT NULL
		AND cp_instance_id IS NOT NULL
		AND parameter_printas IS NOT NULL
		AND bill_date_quarter IS NOT NULL
		AND value_float IS NOT NULL
		AND test_result_id IS NOT NULL
		PRIMARY KEY ((sex, parameter_printas, age_group), bill_date_quarter, value_float, cp_instance_id, test_result_id)
	WITH CLUSTERING ORDER BY (bill_date_quarter DESC, value_float ASC, cp_instance_id ASC, test_result_id ASC);

```

Purpose

- Enables efficient range queries on numerical results
- Facilitates reference range validation

- Example Use case
  ```sql
  select * from case_data_by_value_float
  where sex = 'F'
  and parameter_printas = 'MCV'
  and age_group = 'Neonate'
  and bill_date_quarter = 'q24-04'
  and value_float >= 100 and value_float <= 120;
  and cp_instance_id = '1101'
  ```

### Categorical Results View

```sql
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
		AND age_group is NOT NULL
		AND cp_instance_id IS NOT NULL
		AND parameter_printas IS NOT NULL
		AND bill_date_quarter IS NOT NULL
		AND value_text IS NOT NULL
		AND test_result_id IS NOT NULL
  PRIMARY KEY ((sex, parameter_printas, age_group), bill_date_quarter, value_text, cp_instance_id, test_result_id)
WITH CLUSTERING ORDER BY (bill_date_quarter DESC, value_text ASC, cp_instance_id ASC, test_result_id ASC);
```

Purpose

- Optimizes queries for categorical test results
- Supports pattern matching in text-based results
- Enables efficient filtering of specific result categories
- Example Use case
  ```sql
  select * from case_data_by_value_text
  where sex = 'F'
  and parameter_printas = 'PARASITES'
  and age_group = 'Neonate'
  and bill_date_quarter = 'q24-04'
  and value_text = 'POSITIVE';
  and cp_instance_id = '1101'
  ```

### Billing Analysis View

```sql
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
		AND test_result_id IS NOT NULL
		AND sex IS NOT NULL
		AND age_group IS NOT NULL
		AND bill_date_quarter IS NOT NULL
		AND cp_instance_id IS NOT NULL
		AND parameter_printas IS NOT NULL
  PRIMARY KEY (bill_id, sex, parameter_printas, age_group, bill_date_quarter, cp_instance_id, test_result_id)
WITH CLUSTERING ORDER BY (sex ASC, parameter_printas ASC, age_group ASC, bill_date_quarter DESC, cp_instance_id ASC, test_result_id ASC);
```

Purpose

- Facilitates billing-related queries
- Example Use Case

  ```sql
  select *
  from case_data_by_bill_id
  where bill_id= 'b_241015213103167581105';
  ```
