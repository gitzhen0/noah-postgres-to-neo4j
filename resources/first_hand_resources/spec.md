**Automated RDBMS-to-Knowledge Graph Conversion Bot:**

**Building Intelligent Database Migration Tools for the NOAH Housing
Affordability Case Study**

Student Name: \[Student Name\]

Program: Master of Science in Management and Systems

University: School of Professional Studies, New York University

Date: Spring 2026

Advisor: Dr. Andres Fortino

Sponsor Organization: The Digital Forge Lab

# Abstract

This capstone project proposes the development of an automated bot that
converts relational database management systems (RDBMS) into knowledge
graph databases. The bot will implement proven academic methodologies
including Rel2Graph (Zhao et al., 2023), De Virgilio\'s conversion
framework (2013), and Data2Neo (2024) to systematically transform
relational schemas into property graph models while preserving data
integrity and semantic relationships. The system will feature three core
capabilities: (1) automated schema analysis and intelligent mapping from
tables to nodes/edges, (2) data migration with validation, and (3) a
natural language query interface (Text2Cypher) enabling non-technical
users to query the resulting graph database using plain English. The
project will be validated through conversion of the NOAH (Naturally
Occurring Affordable Housing) Information Dashboard database---a
real-world PostgreSQL database containing NYC housing and demographic
data---into Neo4j. This case study will demonstrate the bot&#x2019;s
ability to handle complex spatial data, multiple table relationships,
and realistic data quality challenges. The ultimate deliverable is a
working prototype that serves dual purposes: (1) a practical tool for
Digital Labs to modernize legacy database systems, and (2) an
educational platform for teaching advanced database concepts in Business
Informatics courses. Success will be measured by complete migration of
the NOAH database with zero data loss, query performance improvements
compared to relational SQL, and student ability to successfully use the
tool in classroom settings.

# Introduction

## Problem Statement

Organizations worldwide maintain critical business data in relational
database management systems (RDBMS) such as PostgreSQL, MySQL, and SQL
Server. While RDBMS excel at transaction processing and data integrity
through foreign key constraints, they face fundamental limitations when
querying highly interconnected data. Queries involving multiple table
joins become computationally expensive and syntactically complex. As
noted by De Virgilio et al. (2013), JOIN operations across three or more
tables can experience significant performance degradation, and the
resulting SQL becomes difficult to write, read, and maintain.

Knowledge graph databases---represented by systems like Neo4j, Amazon
Neptune, and ArangoDB---address these limitations by natively
representing relationships as first-class entities. Graph databases
eliminate JOIN operations through direct edge traversal, enabling
relationship-heavy queries to execute orders of magnitude faster.
However, migrating from relational to graph databases remains a manual,
error-prone, and resource-intensive process. Database administrators
must analyze schemas, design graph models, write custom ETL scripts,
validate data integrity, and often repeat this work for each new
database migration.

Current migration approaches suffer from three critical deficiencies:

- **Time Intensity:** Manual schema analysis and ETL development can
  take weeks or months

- **Error Proneness:** Manual mapping introduces inconsistencies,
  orphaned nodes, and referential integrity violations

- **Non-Reproducibility:** Each migration requires bespoke code, making
  ongoing maintenance and updates difficult

Additionally, even after successful migration, a query accessibility gap
remains: business analysts and policymakers cannot leverage graph
databases without learning specialized query languages like Cypher or
Gremlin, limiting the democratization of data access.

## Motivation

The motivation for this project stems from converging technological,
educational, and business needs:

- **Academic Foundation:** Recent academic research has established
  systematic methodologies for RDBMS-to-graph conversion. Rel2Graph
  (Zhao et al., 2023) demonstrates automated knowledge graph
  construction from multiple databases simultaneously. De Virgilio et
  al. (2013) provide formal conversion patterns exploiting relational
  constraints. Data2Neo (2024) offers open-source Python tooling. These
  proven methodologies can now be synthesized into a practical,
  production-ready system.

- **Real-World Validation Opportunity:** The NOAH Housing Affordability
  database provides an ideal test case. Developed as a previous NYU
  capstone project (Zhang, 2025), it consolidates fragmented NYC housing
  data into a PostgreSQL database with 177 ZIP codes, 100,000+
  buildings, and complex spatial relationships. Converting NOAH to Neo4j
  will demonstrate the bot&#x2019;s capability to handle real-world
  complexity including spatial data types (PostGIS), multi-table joins,
  and realistic data quality issues.

- **Educational Value:** Database migration touches core informatics
  concepts: data modeling, schema design, ETL pipelines, query
  optimization, and AI-powered interfaces. A working conversion bot
  provides hands-on learning for Advanced Business Informatics students,
  connecting theoretical database concepts to practical implementation.

- **Business Utility:** Digital Labs and similar organizations face
  growing pressure to modernize legacy systems. An automated conversion
  bot reduces migration costs, accelerates digital transformation, and
  enables organizations to unlock graph analytics capabilities on
  existing data assets.

- **Democratizing Data Access:** By integrating a Text2Cypher natural
  language interface powered by large language models, the system makes
  graph databases accessible to non-technical users. Policymakers can
  ask questions in plain English rather than learning specialized query
  syntax.

## Project Goal

The overarching goal of this capstone project is to **design, develop,
and rigorously evaluate a working prototype of an automated
RDBMS-to-Knowledge Graph Conversion Bot**, validated through successful
conversion of the NOAH Housing Affordability database from PostgreSQL to
Neo4j. The bot will demonstrate that systematic, automated database
migration is both technically feasible and practically valuable for
organizations seeking to modernize data infrastructure.

Specifically, the project will:

- Implement automated schema introspection and intelligent mapping
  algorithms based on proven academic methodologies

- Build a data migration engine that preserves referential integrity and
  validates correctness

- Integrate a natural language query interface enabling plain-English
  querying of the resulting graph database

- Successfully convert the entire NOAH database (177 ZIP codes, 100,000+
  buildings) with zero data loss

- Demonstrate query performance improvements and relationship-traversal
  advantages over relational SQL

- Produce comprehensive documentation and classroom materials for use in
  Advanced Business Informatics courses

# Background and Core Technologies

## Relational vs. Graph Database Paradigms

Relational databases organize data into tables with rows and columns,
enforcing relationships through foreign keys. This model works well for
transactional systems but struggles with relationship-heavy queries.
Graph databases represent data as nodes (entities) and edges
(relationships), storing relationships as first-class objects. This
enables efficient traversal of connections without expensive JOIN
operations.

The fundamental conversion pattern, established across all major
academic literature, transforms:

- **Tables → Node Labels** (Person table becomes Person nodes)

- **Rows → Individual Nodes** (each row becomes one node)

- **Columns → Node Properties** (attributes stored as key-value pairs)

- **Primary Keys → Node Identifiers** (unique constraints)

- **Foreign Keys → Relationships** (directed edges between nodes)

- **Join Tables → Direct Relationships** (many-to-many becomes edges)

## Academic Foundations

This project builds on three foundational academic works:

- **Rel2Graph (Zhao et al., 2023):** Demonstrates automated knowledge
  graph construction from multiple relational databases with
  SQL-to-Cypher query translation. Validated on Spider and KaggleDBQA
  benchmarks. ArXiv:2310.01080

- **De Virgilio Methodology (2013):** Provides formal conversion
  framework exploiting relational schema constraints. Published in ACM
  GRADES Workshop. Available at
  https://event.cwi.nl/grades/2013/01-DeVirgilio.pdf

- **Data2Neo (2024):** Open-source Python library for Neo4j data
  integration, offering practical implementation patterns.
  ArXiv:2406.04995. GitHub: jkminder/data2neo

## Text2Cypher and Natural Language Interfaces

Recent advances in large language models enable Text2Cypher systems that
translate natural language questions into graph query languages.
Research by Ozsoy et al. (2024) demonstrates that schema-aware LLMs
achieve \>80% accuracy on benchmark datasets. This project will
integrate a Text2Cypher interface allowing users to query converted
graphs using questions like *&#x201C;Which ZIP codes have the highest
rent burden?&#x201D;* or *&#x201C;Show buildings built before 1960 in
high-income neighborhoods.&#x201D;*

## The NOAH Database Case Study

The NOAH (Naturally Occurring Affordable Housing) Information Dashboard
database serves as the validation case for this project. Developed by
Chaoou Zhang (NYU MS Management & Systems, Fall 2025) for Urban Labs,
the database consolidates fragmented NYC housing data into an integrated
PostgreSQL/PostGIS system. It contains:

- 177 NYC ZIP codes/ZCTAs with demographic and affordability indicators

- \~100,000 residential buildings from NYC PLUTO dataset

- Housing metrics: median rent, median income, rent burden, vacancy
  rates

- Spatial relationships and PostGIS geometry types

- Complex join patterns across 12+ tables

Converting NOAH to Neo4j will unlock powerful graph queries such as
*&#x201C;Find all buildings in neighboring ZIP codes of 10012 where rent
burden exceeds 40% of median income,&#x201D;* which would require
complex self-joins and performance-intensive SQL in the relational
model.

# Practical Application: NOAH Housing Database Conversion

## About the NOAH Database

The NOAH (Naturally Occurring Affordable Housing) Information Dashboard
database serves as the primary validation case study for this project.
Developed by Chaoou Zhang (NYU MS Management & Systems, Fall 2025) for
Urban Labs---a nonprofit research organization focused on NYC housing
policy---the database consolidates fragmented housing data into an
integrated PostgreSQL/PostGIS system.

**Database Profile:**

- **Platform:** PostgreSQL 14 with PostGIS spatial extension

- **Scale:** 177 NYC ZIP codes/ZCTAs, \~100,000 residential building
  records

- **Data Sources:** American Community Survey (ACS), NYC PLUTO, HUD data

- **Key Metrics:** Median rent, median income, rent burden rates,
  vacancy rates, building characteristics

- **Complexity:** 12+ tables with multiple foreign key relationships,
  spatial geometries, demographic indicators

## Current Relational Schema (Key Tables)

- **zipcode:** Geographic units with properties including zip_code,
  median_rent, median_income, rent_burden_rate, vacancy_rate

- **building:** Individual structures with BBL identifier, address,
  year_built, num_floors, units_residential, landuse classification.
  Foreign key to zipcode_id.

- **demographic_indicator:** Population metrics with total_population,
  median_age, pct_renter_occupied. Foreign key to zipcode_id.

## Expected Neo4j Graph Schema After Conversion

**Node Types:**

- **(:Zipcode)** --- 177 nodes with properties: zip_code, median_rent,
  median_income, rent_burden_rate, vacancy_rate

- **(:Building)** --- \~100,000 nodes with properties: bbl, address,
  year_built, num_floors, units_residential, landuse

- **(:Demographic)** --- 177 nodes with properties: total_population,
  median_age, pct_renter_occupied

**Relationship Types:**

- **(:Building)-\[:LOCATED_IN\]-\>(:Zipcode)** --- \~100,000
  relationships mapping buildings to their ZIP codes

- **(:Zipcode)-\[:HAS_DEMOGRAPHICS\]-\>(:Demographic)** --- 177
  relationships connecting demographics to geographies

- **(:Zipcode)-\[:NEIGHBORS\]-\>(:Zipcode)** --- Spatial adjacency
  relationships (to be derived from PostGIS geometries)

## Example Graph Queries Enabled by Conversion

Converting NOAH to Neo4j will enable powerful relationship-traversal
queries that are cumbersome in the relational model:

***Query 1: Spatial Relationship Traversal***

**Natural Language:** *\"Show me all residential buildings in ZIP codes
neighboring 10012 that were built before 1960.\"*

**Relational SQL Challenge:** Requires complex self-join on zipcode
table to find neighbors, then JOIN to building table---inefficient and
syntactically complex.

**Graph Cypher Solution:**

MATCH (z:Zipcode {zip_code:
\'10012\'})-\[:NEIGHBORS\]-(neighbor:Zipcode)
-\[:CONTAINS\]-\>(b:Building) WHERE b.year_built \< 1960 RETURN
b.address, b.year_built, neighbor.zip_code

***Query 2: Multi-Criteria Affordability Analysis***

**Natural Language:** *\"Find ZIP codes where median rent exceeds 40% of
median income AND vacancy rate is below 5%.\"*

**Graph Cypher Solution:**

MATCH (z:Zipcode) WHERE z.median_rent \> (z.median_income \* 0.4) AND
z.vacancy_rate \< 0.05 RETURN z.zip_code, z.median_rent,
z.median_income, z.rent_burden_rate ORDER BY z.rent_burden_rate DESC

***Query 3: Building-Level Pattern Detection***

**Natural Language:** *\"How many pre-1980 buildings are located in
high-rent-burden neighborhoods?\"*

**Graph Cypher Solution:**

MATCH (b:Building)-\[:LOCATED_IN\]-\>(z:Zipcode) WHERE b.year_built \<
1980 AND z.rent_burden_rate \> 0.3 RETURN z.zip_code, count(b) AS
old_buildings ORDER BY old_buildings DESC

## Why NOAH is an Ideal Test Case

The NOAH database provides an ideal validation case for this conversion
bot because it represents real-world complexity:

- **Realistic Scale:** 100,000+ records test the bot\'s ability to
  handle production-sized datasets efficiently

- **Spatial Data Complexity:** PostGIS geometries require special
  handling, demonstrating the bot\'s adaptability to non-standard data
  types

- **Multi-Table Relationships:** Foreign keys across entity and join
  tables validate comprehensive schema mapping capabilities

- **Data Quality Challenges:** Missing values, inconsistencies, and edge
  cases mirror real-world data migration scenarios

- **Clear Use Case:** Housing affordability analysis provides concrete
  graph queries that demonstrate relationship-traversal advantages

- **Educational Value:** NYC housing data is accessible and relevant to
  students, making it an engaging classroom example

# Project Objectives

## Overall Objective

The overall objective is to **design, develop, and rigorously evaluate a
working prototype conversion bot** that automates
RDBMS-to-knowledge-graph migration, validated through successful
conversion of the NOAH database and demonstrating measurable
improvements in query performance and data accessibility compared to the
original relational implementation.

## Specific Objectives (SMART)

- **Specific:** Design and implement a schema introspection module that
  automatically analyzes relational database metadata (tables, columns,
  keys, constraints) and classifies structural patterns (entity tables
  vs. join tables).

- **Measurable:** Build an intelligent mapping engine that applies
  transformation rules to generate Neo4j-compatible graph schemas,
  including node labels, relationship types, property definitions, and
  constraint specifications.

- **Achievable:** Develop a data migration engine that extracts
  relational data, transforms it according to the mapping, and loads it
  into Neo4j with full referential integrity validation.

- **Relevant:** Integrate a Text2Cypher natural language query interface
  that enables plain-English querying of the converted graph database,
  achieving \>75% accuracy on a benchmark set of 20 representative
  questions about NOAH data.

- **Time-bound:** Successfully migrate the complete NOAH database (177
  ZIP codes, 100,000+ buildings, all relationships) to Neo4j within the
  12-week project timeline, with zero data loss and full validation of
  row counts and referential integrity.

- Produce comprehensive documentation including system architecture,
  usage guides, classroom materials (tutorials, exercises, sample
  queries), and a final capstone report suitable for submission to the
  NYU SPS MASY program.

- Demonstrate measurable query performance improvements: compare
  execution time and code complexity for equivalent
  relationship-traversal queries in PostgreSQL (JOIN-based) vs. Neo4j
  (graph-traversal).

# Expected Outcomes and Contributions

## Tangible Deliverables

- **Working Conversion Bot Prototype:** Functional Python-based tool
  capable of automated RDBMS-to-graph conversion

- **NOAH Database Successfully Converted:** Complete migration from
  PostgreSQL to Neo4j with validation report

- **Text2Cypher Query Interface:** Natural language query system
  achieving \>75% accuracy on benchmark questions

- **Performance Comparison Analysis:** Documented query performance
  improvements and complexity reduction

- **Comprehensive Documentation:** Architecture docs, user guide, API
  reference, deployment instructions

- **Educational Materials:** Tutorials, lab exercises, Jupyter notebooks
  for classroom use

- **Final Capstone Report:** 10-12 page document meeting NYU SPS MASY
  requirements

- **GitHub Repository:** Open-source codebase with clear documentation
  and examples

## Practical Implications

This project provides immediate practical value to Digital Labs by
delivering a reusable tool for database modernization. The bot will
enable systematic, repeatable migrations from legacy RDBMS to modern
graph databases, reducing migration costs and accelerating digital
transformation initiatives. The modular architecture allows for
continuous improvement and adaptation to different database systems
beyond PostgreSQL and Neo4j.

The NOAH conversion demonstrates the bot&#x2019;s ability to handle
real-world complexity including spatial data, complex relationships, and
data quality challenges. This validation provides confidence for
applying the tool to other organizational databases. The integrated
Text2Cypher interface democratizes data access, enabling business users
and policymakers to leverage graph analytics without specialized
training.

## Educational Contributions

The project serves as a comprehensive case study for Advanced Business
Informatics courses, integrating multiple core concepts:

- **Database Theory:** Comparing relational and graph data models,
  understanding trade-offs

- **Data Engineering:** ETL pipelines, schema design, data validation,
  quality assurance

- **AI Integration:** Using LLMs for query translation, understanding
  prompt engineering

- **Real-World Problem Solving:** Working with actual NYC housing data,
  addressing practical challenges

Students will gain hands-on experience with cutting-edge technologies
while learning systematic approaches to database migration---skills
directly applicable to industry roles in data engineering and business
intelligence.

## Broader Impact

Beyond immediate project deliverables, this work contributes to the
broader field of database modernization by demonstrating that automated,
intelligent conversion is achievable using open-source tools and proven
academic methodologies. The project provides a replicable pattern that
other organizations can adapt to their own migration needs. By
open-sourcing the code and documentation, the project contributes to the
growing ecosystem of graph database tools and accelerates adoption of
knowledge graph technologies across industries.

# Evaluation Criteria

The project will be evaluated based on the following criteria aligned
with NYU SPS MASY capstone requirements:

- **Technical Completeness:** Does the prototype implement all core
  components (schema inspection, mapping, migration, Text2Cypher)? Are
  all components functional and properly integrated?

- **Validation Success:** Is the NOAH database successfully converted
  with zero data loss? Do validation checks confirm referential
  integrity?

- **Performance Demonstration:** Does the project demonstrate measurable
  query performance improvements? Is the comparison methodology rigorous
  and well-documented?

- **Natural Language Interface Accuracy:** Does the Text2Cypher module
  achieve \>75% accuracy on benchmark questions? Are errors
  well-understood and documented?

- **Documentation Quality:** Is system architecture clearly documented?
  Are usage instructions complete and understandable? Is the final
  report comprehensive and well-written?

- **Educational Materials:** Are classroom materials suitable for
  Advanced Business Informatics courses? Can students with moderate
  technical skills successfully use the tool?

- **Project Management:** Was the project completed within the 12-week
  timeline? Were milestones met? Was scope managed effectively?

- **Integration of Learning:** Does the project demonstrate mastery of
  MASY program concepts including systems thinking, technology
  management, data governance, and ethical considerations?

- **Presentation Quality:** Is the final presentation clear, engaging,
  and professionally delivered? Does it effectively communicate key
  findings to both technical and non-technical audiences?

- **Practical Utility:** Does the deliverable address a real need for
  Digital Labs? Is the tool usable and maintainable? Does it provide
  tangible business value?

# References

Zhao, F., et al. (2023). *Rel2Graph: Automated Mapping From Relational
Databases to a Unified Property Knowledge Graph.* arXiv:2310.01080.

De Virgilio, R., Maccioni, A., & Torlone, R. (2013). *Converting
Relational to Graph Databases.* ACM GRADES Workshop.
https://event.cwi.nl/grades/2013/01-DeVirgilio.pdf

Minder, J.K., et al. (2024). *Data2Neo: A Tool for Complex Neo4j Data
Integration.* arXiv:2406.04995. GitHub: jkminder/data2neo

Ozsoy, M.G., et al. (2024). *Text2Cypher: Bridging Natural Language and
Graph Databases.* arXiv:2412.10064.

Neo4j Documentation. *Modeling: Relational to Graph.*
https://neo4j.com/docs/getting-started/data-modeling/relational-to-graph-modeling/

Zhang, C. (2025). *NOAH Information Dashboard: A Proof-of-Concept
Housing Affordability Analytics Tool for Urban Labs.* Applied Project
Final Report, NYU Stern School of Business.

*--- End of Specification ---*
