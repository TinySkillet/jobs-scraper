from __future__ import annotations

from jobscraper.models import RoleSearchConfig, SearchSpec


def _linkedin_search(name: str, term: str) -> SearchSpec:
    return SearchSpec(name=f"linkedin_{name}", term=term, provider="linkedin")


ROLE_CATALOG = {
    "java": RoleSearchConfig(
        role="java",
        final_output_name="jobs_final_java.csv",
        searches=(
            SearchSpec(
                "java_engineer",
                '("java developer" OR "java engineer" OR "java software engineer" OR "backend java") (spring OR "spring boot" OR microservices) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_developer",
                '("java developer" OR "java application developer") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_software_engineer",
                '("java software engineer" OR "software engineer java") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "spring_backend",
                '("spring boot developer" OR "spring developer" OR "java backend developer" OR "backend java developer") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_microservices",
                '(java OR "spring boot") (microservices OR "rest api" OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "backend_java",
                '("backend developer" OR "backend engineer" OR "software engineer") (java OR spring OR "spring boot") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_api",
                '(java OR "spring boot") (api OR kafka OR aws OR kubernetes) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "junior_java",
                '(java OR spring OR "spring boot") (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "software engineer I" OR "developer I") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "mid_level_java",
                '(java OR spring OR "spring boot") ("mid level" OR "mid-level" OR intermediate OR "software engineer II" OR "developer II" OR "java developer II") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_rest_api",
                '("java developer" OR "java software engineer" OR "backend engineer") ("REST API" OR "RESTful API" OR "web services" OR "microservices") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_cloud",
                '("java developer" OR "java software engineer" OR "backend java developer") (AWS OR Azure OR GCP OR cloud OR Kubernetes OR Docker) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "enterprise_java",
                '("java developer" OR "software developer") (J2EE OR Jakarta OR Hibernate OR Maven OR Gradle OR Tomcat) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "jvm_backend",
                '("backend engineer" OR "backend developer" OR "software engineer") (JVM OR Java OR Kotlin) (Spring OR "Spring Boot" OR microservices OR API) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_fintech_enterprise",
                '(java OR "spring boot") (fintech OR banking OR payments OR enterprise OR "distributed systems") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            _linkedin_search("java_developer", "Java Developer"),
            _linkedin_search("java_software_engineer", "Java Software Engineer"),
            _linkedin_search("spring_boot_developer", "Spring Boot Developer"),
            _linkedin_search("backend_java_engineer", "Backend Java Engineer"),
        ),
    ),
    "fullstack": RoleSearchConfig(
        role="fullstack",
        final_output_name="jobs_final_fullstack.csv",
        searches=(
            SearchSpec(
                "fullstack_engineer",
                '("full stack developer" OR "full stack engineer" OR "full-stack developer" OR "full-stack engineer" OR fullstack) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "fullstack_frontend",
                '("full stack" OR "full-stack" OR fullstack) (react OR angular OR javascript OR typescript OR node) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "react_node",
                '("react developer" OR "react engineer") (node OR "node.js" OR express OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "typescript_node",
                '(typescript OR javascript) (node OR "node.js" OR express) ("full stack" OR fullstack OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "frontend_backend",
                '("front end" OR frontend OR react OR angular) (backend OR "back end" OR api) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "mern_stack",
                '(mern OR "mongo express react node" OR "react node") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "software_engineer_react_node",
                '("software engineer" OR developer) (react OR angular OR typescript OR javascript) (node OR "node.js" OR backend OR api) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "web_application_developer",
                '("web application developer" OR "web developer" OR "application developer") (react OR angular OR node OR "full stack" OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "javascript_fullstack",
                '(javascript OR typescript) ("full stack" OR fullstack OR backend OR api) (react OR angular OR node) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "angular_node",
                '(angular OR react) (node OR "node.js" OR api OR backend) ("software engineer" OR developer) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "junior_fullstack",
                '("full stack" OR fullstack OR react OR angular OR node OR typescript) (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "software engineer I" OR "developer I") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "mid_level_fullstack",
                '("full stack" OR fullstack OR react OR angular OR node OR typescript) ("mid level" OR "mid-level" OR intermediate OR "software engineer II" OR "developer II" OR "full stack developer II") -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "nextjs_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Next.js OR NextJS OR React) (Node OR "node.js" OR API OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "vue_node",
                '(Vue OR Vue.js OR Nuxt OR Nuxt.js) (Node OR "node.js" OR backend OR API OR "full stack" OR fullstack) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "java_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Java OR "Spring Boot") (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "dotnet_fullstack",
                '("full stack" OR fullstack OR "software engineer") (.NET OR "C#" OR ASP.NET) (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "python_fullstack",
                '("full stack" OR fullstack OR "software engineer") (Python OR Django OR Flask OR FastAPI) (React OR Angular OR Vue OR JavaScript OR TypeScript) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            SearchSpec(
                "frontend_api_engineer",
                '("software engineer" OR developer) (React OR Angular OR Vue OR TypeScript OR JavaScript) (REST OR GraphQL OR API OR backend) -intern -internship -android -mobile -qa -tester -salesforce',
            ),
            _linkedin_search("fullstack_developer", "Full Stack Developer"),
            _linkedin_search("fullstack_engineer", "Full Stack Engineer"),
            _linkedin_search("react_node_developer", "React Node Developer"),
            _linkedin_search("frontend_backend_engineer", "Frontend Backend Engineer"),
        ),
    ),
    "data_engineer": RoleSearchConfig(
        role="data_engineer",
        final_output_name="jobs_final_data_engineer.csv",
        searches=(
            SearchSpec(
                "data_engineer",
                '("data engineer" OR "data engineering" OR "big data engineer") (python OR sql OR spark OR airflow OR dbt OR databricks OR snowflake) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "etl_pipeline",
                '("etl developer" OR "etl engineer" OR "data pipeline engineer" OR "pipeline engineer") (python OR sql OR spark OR airflow OR aws OR azure OR gcp) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "analytics_engineer",
                '("analytics engineer" OR "data warehouse engineer" OR "data platform engineer") (sql OR dbt OR snowflake OR bigquery OR redshift OR databricks) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "spark_data_engineer",
                '("data engineer" OR "big data engineer") (spark OR pyspark OR databricks) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "snowflake_dbt",
                '("data engineer" OR "analytics engineer") (snowflake OR dbt OR "data warehouse") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "airflow_pipeline",
                '("data engineer" OR "pipeline engineer" OR "etl engineer") (airflow OR orchestration OR "data pipeline") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "python_data_engineer",
                '("data engineer" OR "etl engineer") (python OR pyspark) (sql OR spark OR airflow OR cloud) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "sql_data_engineer",
                '("data engineer" OR "analytics engineer") (sql OR "data warehouse") (python OR dbt OR snowflake OR bigquery) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "junior_data_engineer",
                '("data engineer" OR "etl developer" OR "etl engineer" OR "analytics engineer" OR "data pipeline") (junior OR associate OR "entry level" OR "early career" OR "new grad" OR "engineer I" OR "developer I") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "mid_level_data_engineer",
                '("data engineer" OR "etl developer" OR "etl engineer" OR "analytics engineer" OR "data pipeline") ("mid level" OR "mid-level" OR intermediate OR "engineer II" OR "developer II" OR "data engineer II") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "cloud_data_engineer",
                '("data engineer" OR "data platform engineer" OR "etl engineer") (AWS OR Azure OR GCP OR Glue OR "Data Factory" OR "Cloud Composer") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "lakehouse_engineer",
                '("data engineer" OR "data platform engineer") (lakehouse OR "data lake" OR Delta OR Iceberg OR Hive OR "Apache Hudi") -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "streaming_data_engineer",
                '("data engineer" OR "streaming data engineer" OR "data platform engineer") (Kafka OR Flink OR streaming OR Kinesis OR Pub/Sub) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "data_infrastructure_engineer",
                '("data infrastructure engineer" OR "data platform engineer" OR "platform data engineer") (Python OR SQL OR Spark OR Airflow OR Kubernetes) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "warehouse_bi_data_engineer",
                '("data engineer" OR "analytics engineer" OR "BI engineer") (Snowflake OR BigQuery OR Redshift OR dbt OR Looker OR Tableau) -intern -internship -qa -tester -salesforce',
            ),
            SearchSpec(
                "azure_data_engineer",
                '("data engineer" OR "etl developer" OR "analytics engineer") (Azure OR "Azure Data Factory" OR Synapse OR Databricks OR Fabric) -intern -internship -qa -tester -salesforce',
            ),
            _linkedin_search("data_engineer", "Data Engineer"),
            _linkedin_search("etl_engineer", "ETL Engineer"),
            _linkedin_search("analytics_engineer", "Analytics Engineer"),
            _linkedin_search("data_platform_engineer", "Data Platform Engineer"),
        ),
    ),
    "application_security": RoleSearchConfig(
        role="application_security",
        final_output_name="jobs_final_application_security.csv",
        searches=(
            SearchSpec(
                "application_security_engineer",
                '("application security engineer" OR "appsec engineer" OR "application security analyst" OR "application security") (secure OR vulnerability OR OWASP OR SAST OR DAST OR "code review") -staff -principal -lead -manager -director -intern -internship -soc -physical',
            ),
            SearchSpec(
                "product_security_engineer",
                '("product security engineer" OR "software security engineer" OR "secure coding engineer" OR "software security") (application OR software OR API OR cloud) -staff -principal -lead -manager -director -intern -internship -soc -physical',
            ),
            SearchSpec(
                "secure_code_review",
                '("secure code review" OR "security code review" OR "threat modeling" OR "secure coding") (engineer OR analyst OR consultant OR developer) -staff -principal -lead -manager -director -intern -internship -soc -physical',
            ),
            SearchSpec(
                "web_application_security",
                '("web application security" OR "api security" OR "application security" OR OWASP OR SAST OR DAST) (engineer OR analyst OR consultant OR developer) -staff -principal -lead -manager -director -intern -internship -soc -physical',
            ),
            SearchSpec(
                "security_engineer_appsec",
                '("security engineer" OR "software engineer" OR developer) ("application security" OR appsec OR OWASP OR SAST OR DAST OR "secure code" OR "API security") -staff -principal -lead -manager -director -intern -internship -soc -physical',
            ),
            _linkedin_search("application_security_engineer", "Application Security Engineer"),
            _linkedin_search("product_security_engineer", "Product Security Engineer"),
            _linkedin_search("appsec_engineer", "AppSec Engineer"),
        ),
    ),
    "penetration_tester": RoleSearchConfig(
        role="penetration_tester",
        final_output_name="jobs_final_penetration_tester.csv",
        searches=(
            SearchSpec(
                "penetration_tester",
                '("penetration tester" OR "penetration testing" OR "pen tester" OR pentester) (web OR network OR application OR cloud) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "offensive_security",
                '("offensive security engineer" OR "offensive security consultant" OR "ethical hacker") (penetration OR exploit OR vulnerability OR redteam OR "red team") -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "web_app_pentest",
                '("web application penetration testing" OR "application penetration tester" OR "web app pentest") (Burp OR OWASP OR API OR cloud) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "vulnerability_assessment",
                '("vulnerability assessment" OR "security assessment") ("penetration testing" OR pentest OR "ethical hacking") -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            _linkedin_search("penetration_tester", "Penetration Tester"),
            _linkedin_search("penetration_testing_consultant", "Penetration Testing Consultant"),
            _linkedin_search("offensive_security_engineer", "Offensive Security Engineer"),
        ),
    ),
    "cybersecurity": RoleSearchConfig(
        role="cybersecurity",
        final_output_name="jobs_final_cybersecurity.csv",
        searches=(
            SearchSpec(
                "cybersecurity_engineer",
                '("cybersecurity engineer" OR "cyber security engineer" OR "information security engineer") (cloud OR SIEM OR vulnerability OR incident OR IAM) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "security_analyst",
                '("security analyst" OR "cybersecurity analyst" OR "information security analyst") (SIEM OR SOC OR incident OR threat OR vulnerability) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "cloud_security",
                '("cloud security engineer" OR "security engineer") (AWS OR Azure OR GCP OR IAM OR Kubernetes OR cloud) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            SearchSpec(
                "security_operations",
                '("security operations" OR SOC OR "incident response" OR "threat detection") (analyst OR engineer OR specialist) -staff -senior -principal -lead -manager -director -intern -internship -physical',
            ),
            _linkedin_search("cybersecurity_engineer", "Cybersecurity Engineer"),
            _linkedin_search("security_analyst", "Security Analyst"),
            _linkedin_search("cloud_security_engineer", "Cloud Security Engineer"),
        ),
    ),
}
