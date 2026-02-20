Urban Lab Affordable Housing Dashboard: A Data Portal for NYC

Applied Project Final Report

By

Yue Yu

Fall Semester, 2025

A paper submitted in partial fulfillment of the requirements for the
degree of

Master of Science in Management and Analytics

at the

Division of Programs in Business

School of Professional Studies

New York University

*\*

Table of Contents

[Declaration](#declaration)

[Acknowledgments](#acknowledgments)

[Abstract](#abstract)

[Abbreviations And Definitions](#abbreviations-and-definitions)

[1. Introduction [1](#introduction)](#introduction)

[1.1 Problem [1](#problem)](#problem)

[1.2 Approach [1](#approach)](#approach)

[1.3 Core Technology [2](#core-technology)](#core-technology)

[1.4 Benefits [2](#benefits)](#benefits)

[1.5 Research Question [2](#research-question)](#research-question)

[1.6 Contribution [3](#contribution)](#contribution)

[1.7 Sponsor [3](#sponsor)](#sponsor)

[1.8 Importance Of Project
[3](#importance-of-project)](#importance-of-project)

[2. Project Objectives And Metrics
[4](#project-objectives-and-metrics)](#project-objectives-and-metrics)

[2.1 Goal of the Project
[4](#goal-of-the-project)](#goal-of-the-project)

[2.2 Project Deliverables and Metrics
[4](#project-deliverables-and-metrics)](#project-deliverables-and-metrics)

[2.3 Project Evaluation [5](#project-evaluation)](#project-evaluation)

[3. Alternate Solutions Evaluated
[6](#alternate-solutions-evaluated)](#alternate-solutions-evaluated)

[3.1 Solution Evaluation Criteria
[6](#solution-evaluation-criteria)](#solution-evaluation-criteria)

[3.1.1 React frontend with Mapbox GL Js or Leaflet
[6](#react-frontend-with-mapbox-gl-js-or-leaflet)](#react-frontend-with-mapbox-gl-js-or-leaflet)

[3.1.2 Flask instead of FastAPI for backend services
[6](#flask-instead-of-fastapi-for-backend-services)](#flask-instead-of-fastapi-for-backend-services)

[3.1.3 Geopandas for Spatial Processing
[7](#geopandas-for-spatial-processing)](#geopandas-for-spatial-processing)

[3.1.4 BI Tools such as Apache Superset or Tableau
[7](#bi-tools-such-as-apache-superset-or-tableau)](#bi-tools-such-as-apache-superset-or-tableau)

[3.2 Solution Evaluation Criteria
[8](#solution-evaluation-criteria-1)](#solution-evaluation-criteria-1)

[3.3 Selection Rationale
[8](#selection-rationale)](#selection-rationale)

[4. Literature Survey [9](#literature-survey)](#literature-survey)

[4.1 Introduction [9](#introduction-1)](#introduction-1)

[4.2 Industry [9](#the-industry)](#the-industry)

[4.3 Problem [10](#the-problem)](#the-problem)

[4.4 Proposed Solution [10](#proposed-solution)](#proposed-solution)

[4.5 Technology [11](#the-technology)](#the-technology)

[4.6 Use Cases [11](#use-cases)](#use-cases)

[4.7 Conclusion [12](#conclusion)](#conclusion)

[5. Approach And Methodology
[13](#approach-and-methodology)](#approach-and-methodology)

[5.1 Problem Statement and Research Question
[13](#problem-statement-and-research-question)](#problem-statement-and-research-question)

[5.2 Proof of Concept Approach
[13](#proof-of-concept-approach)](#proof-of-concept-approach)

[5.3 Technology Trial Plan
[14](#technology-trial-plan)](#technology-trial-plan)

[5.4 Population/Data [14](#_Toc215500436)](#_Toc215500436)

[5.4.1 Rent Burden
[14](#rent-burden-acs-5-year-estimates)](#rent-burden-acs-5-year-estimates)

[5.4.2 Income
[15](#income-acs-5-year-estimates)](#income-acs-5-year-estimates)

[5.4.3 Market Rent
[15](#market-rent-streeteasy)](#market-rent-streeteasy)

[5.4.4 Demographics
[15](#demographics-acs-5-year-estimates)](#demographics-acs-5-year-estimates)

[5.4.5 Geographic Data and Crosswalks
[15](#geographic-data-and-crosswalks)](#geographic-data-and-crosswalks)

[5.5 Procedures [16](#procedures)](#procedures)

[5.5.1 Data Harmonization via Crosswalks
[16](#data-harmonization-via-crosswalks)](#data-harmonization-via-crosswalks)

[5.5.2 ETL Workflow
[16](#etl-workflow-python-pandas-sql)](#etl-workflow-python-pandas-sql)

[5.5.3 Database Schema
[17](#database-schema-postgresqlpostgis)](#database-schema-postgresqlpostgis)

[5.5.4 API Architecture
[17](#api-architecture-fastapi)](#api-architecture-fastapi)

[5.5.5 Dashboard Visualization
[17](#dashboard-visualization-streamlit-pydeck)](#dashboard-visualization-streamlit-pydeck)

[5.5.6 Deployment
[18](#deployment-render-streamlit-cloud-docker)](#deployment-render-streamlit-cloud-docker)

[5.5.7 Technology Trial Summary
[18](#technology-trial-summary)](#technology-trial-summary)

[5.6 Organizational Change Plan
[18](#organizational-change-plan)](#organizational-change-plan)

[6. Results [19](#results)](#results)

[6.1 data processing [19](#data-processing)](#data-processing)

[6.1.1 Data acquisition and Initial Cleaning
[19](#data-acquisition-and-initial-cleaning)](#data-acquisition-and-initial-cleaning)

[6.1.2 Database Schema Creation
[19](#database-schema-creation)](#database-schema-creation)

[6.1.3 ETL Processing using Python + Sql
[19](#etl-processing-using-python-sql)](#etl-processing-using-python-sql)

[6.1.4 Database-Level Transformations
[20](#database-level-transformations)](#database-level-transformations)

[6.2 Outcomes [21](#outcomes)](#outcomes)

[6.2.1 Page 1 - App Page [21](#page-1---app-page)](#page-1---app-page)

[6.2.2 Page 2 - Analysis Page
[25](#page-2---analysis-page)](#page-2---analysis-page)

[6.2.3 Page 3 - Rent Burden Page
[30](#page-3---rent-burden-page)](#page-3---rent-burden-page)

[6.3 Findings [32](#findings)](#findings)

[6.4 Summary Statistics [33](#summary-statistics)](#summary-statistics)

[6.5 Implications [34](#implications)](#implications)

[6.5.1 Practical Implications
[34](#practical-implications)](#practical-implications)

[6.5.2 Theoretical Implications
[34](#theoretical-implications)](#theoretical-implications)

[6.6 Summary [34](#summary)](#summary)

[6.7 Repository of Datasets and Code
[35](#repository-of-data-sets-and-code)](#repository-of-data-sets-and-code)

[7. Issues Encountered [36](#issues-encountered)](#issues-encountered)

[7.1 Data Quality and Inconsistent Formats
[36](#data-quality-and-inconsistent-formats)](#data-quality-and-inconsistent-formats)

[7.2 Geographic Misalignment between Tract-Level and Zip-Level Data
[36](#geographic-misalignment-between-tract-level-and-zip-level-data)](#geographic-misalignment-between-tract-level-and-zip-level-data)

[7.3 Sql Table Creation Errors and Cloud Database Upload Failures
[37](#sql-table-creation-errors-and-cloud-database-upload-failures)](#sql-table-creation-errors-and-cloud-database-upload-failures)

[7.4 Spatial Rendering Issues in Pydeck
[37](#spatial-rendering-issues-in-pydeck)](#spatial-rendering-issues-in-pydeck)

[7.5 Api Connectivity and Deployment Limitations
[38](#api-connectivity-and-deployment-limitations)](#api-connectivity-and-deployment-limitations)

[7.6 Project Scope Adjustment
[38](#project-scope-adjustment)](#project-scope-adjustment)

[7.7 Risk Management Plan
[39](#risk-management-plan)](#risk-management-plan)

[8. Lessons Learned [40](#lessons-learned)](#lessons-learned)

[9. Conclusion And Further Work
[41](#conclusion-and-further-work)](#conclusion-and-further-work)

[9.1 Conclusions [41](#conclusions)](#conclusions)

[9.1.1 Overall Outcomes [41](#overall-outcomes)](#overall-outcomes)

[9.1.2 Key Findings [41](#key-findings)](#key-findings)

[9.1.3 Viability Assessment
[41](#viability-assessment)](#viability-assessment)

[9.2 Implications [42](#implications-1)](#implications-1)

[9.2.1 Theoretical Implications
[42](#theoretical-implications-1)](#theoretical-implications-1)

[9.2.2 Practical Implications
[42](#practical-implications-1)](#practical-implications-1)

[9.3 Limitations [42](#limitations)](#limitations)

[9.3.1 Constraints [42](#constraints)](#constraints)

[9.3.2 Validity And Bias [43](#validity-and-bias)](#validity-and-bias)

[9.3.3 Limitations Of Generative AI For Business Process Re-Engineering
[43](#limitations-of-generative-ai-for-business-process-re-engineering)](#limitations-of-generative-ai-for-business-process-re-engineering)

[9.4 Further Work [43](#further-work)](#further-work)

[9.4.1 Next Steps [43](#next-steps)](#next-steps)

[9.4.2 Long-Term Directions
[44](#long-term-directions)](#long-term-directions)

[9.5 Closing Summary [44](#closing-summary)](#closing-summary)

[References [45](#references)](#references)

[Appendix A - Project Acceptance Document
[47](#appendix-a---project-acceptance-document)](#appendix-a---project-acceptance-document)

[Appendix B - Project Sponsor Agreement
[48](#appendix-b---project-sponsor-agreement)](#appendix-b---project-sponsor-agreement)

[Appendix C -- Functional Requirements Specifications
[54](#appendix-c-functional-requirements-specifications)](#appendix-c-functional-requirements-specifications)

[Appendix D - Project Plan
[57](#appendix-d---project-plan)](#appendix-d---project-plan)

[Appendix E - Risk Management Plan
[60](#appendix-e---risk-management-plan)](#appendix-e---risk-management-plan)

[Appendix F -- Organizational Change Management Plan
[63](#appendix-f-organizational-change-management-plan)](#appendix-f-organizational-change-management-plan)

[Appendix G -- Technology Trial Plan
[66](#appendix-g-technology-trial-plan)](#appendix-g-technology-trial-plan)

[Appendix H - Status Reports
[68](#appendix-h---status-reports)](#appendix-h---status-reports)

[Appendix I - Annotated Bibliography
[76](#appendix-i---annotated-bibliography)](#appendix-i---annotated-bibliography)

#  {#section .TOC-Heading}

# Table of Figures  {#table-of-figures .TOC-Heading}

[Figure 6‑1 Introduction of App Page
[21](#_Toc215500358)](#_Toc215500358)

[Figure 6‑2 Interactive Map [22](#_Toc215500359)](#_Toc215500359)

[Figure 6‑3 Result 1 of "Search by Project ID"
[23](#_Toc215500360)](#_Toc215500360)

[Figure 6‑4 Result 2 of "Search by Project ID"
[24](#_Toc215500361)](#_Toc215500361)

[Figure 6‑5 Data Download Function [24](#_Toc215500362)](#_Toc215500362)

[Figure 6‑6 Analysis Dashboard, Value lookup
[25](#_Toc215500363)](#_Toc215500363)

[Figure 6‑7 Analysis Dashboard, Most Critical Areas, Outlook
[26](#_Toc215500364)](#_Toc215500364)

[Figure 6‑8 Analysis Dashboard, Most Critical Areas, Table Operation
[26](#_Toc215500365)](#_Toc215500365)

[Figure 6‑9 Median Rent Map [27](#_Toc215500366)](#_Toc215500366)

[Figure 6‑10 Median Income Map [28](#_Toc215500367)](#_Toc215500367)

[Figure 6‑11Rent Burden Map [29](#_Toc215500368)](#_Toc215500368)

[Figure 6‑12 Rent Burden Dashboard, Summary Statistics
[30](#_Toc215500369)](#_Toc215500369)

[Figure 6‑13 Rent Burden Dashboard, Rent Burden Histogram
[30](#_Toc215500370)](#_Toc215500370)

[Figure 6‑14 Income Rent Burden Distribution, All Borough
[31](#_Toc215500371)](#_Toc215500371)

[Figure 6‑15 Income Rent Burden Distribution, Manhattan
[31](#_Toc215500372)](#_Toc215500372)

#  {#section-1 .TOC-Heading}

# Declaration

I, *Yue Yu*, declare that this project report submitted by me to School
of Professional Studies, New York University in partial fulfillment of
the requirement for the award of the degree of Master of Science in
Management and Analytics is a record of project work carried out be me
under the guidance of *Professor Matthew Kwatinetz, Clinical Assistant
Professor, NYU Urban Lab**.***

I grant powers of discretion to the Division of Programs in Business,
School of Professional Studies, and New York University to allow this
report to be copied in part or in full without further reference to me.
The permission covers only copies made for study purposes or for
inclusion in Division of Programs in Business, School of Professional
Studies, and New York University research publications, subject to
normal conditions of acknowledgment.

I further declare that the work reported in this project has not been
submitted and will not be submitted, either in part or in full, for the
award of any other degree or diploma in this institute or any other
institute or university.

# Acknowledgments

I would like to sincerely thank Professor Matthew Kwatinetz for his
guidance, insights, and ongoing support as the sponsor of this project.
His feedback throughout the development of the Urban Lab Affordable
Housing Dashboard was invaluable.

I also want to express my appreciation to Professor Andres Fortino and
the faculty members in the Management and Systems program. The knowledge
and skills gained through my coursework directly shaped the technical
and analytical foundations of this project.

Finally, I am grateful to the Urban Lab team for their collaboration and
for providing the opportunity to work on a meaningful project with
real-world impact.

# Abstract

New York City's affordable housing data is scattered across multiple
public sources, making it difficult for researchers and policymakers to
efficiently analyze rent, income, and housing affordability at a
consistent geographic scale. This project addresses this problem by
developing an integrated and geospatially harmonized data platform---a
web-based dashboard---that consolidates income, market rent, rent
burden, and affordable housing supply into a single interactive system.
The proposed solution combines a spatial PostgreSQL/PostGIS database, a
structured data cleaning and integration workflow, and a Streamlit-based
visualization interface to create a unified and accessible data
environment. The proof of concept aims to demonstrate that fragmented
NYC housing indicators can be standardized and delivered through a
user-friendly, map-driven interface.

To accomplish this, the project implemented dataset acquisition from
public sources, manual and script-assisted cleaning and transformation
procedures, geographic crosswalk harmonization, and a spatial database
architecture using PostgreSQL/PostGIS. The dashboard visualizes
ZIP-level affordability metrics, integrates filtering tools, and
provides downloadable datasets for further analysis. A technology trial
compared unstructured data handling with the standardized ETL workflow,
evaluating improvements in processing consistency, error reduction, and
overall analytical reliability.

Results show that the structured ETL workflow significantly improved
data consistency, produced harmonized ZIP-level indicators across all
datasets, and enabled stable map rendering and responsive querying
within the dashboard. These findings confirm that systematic cleaning
and geospatial harmonization enhance data reliability and allow clearer
insight into affordability disparities across NYC.

The results also indicate that a consolidated geospatial framework can
meaningfully improve the usability of open housing data for policy
research and planning. Future work may incorporate temporal trend
analysis, automated ETL pipelines, predictive modeling, and additional
modules such as housing complaints and displacement risk. In the long
term, the system can be scaled to other cities and adapted for broader
housing policy evaluation. Overall, the project demonstrates a
replicable approach to transforming fragmented public datasets into
coherent, decision-ready urban analytics tools.

Dashboard URL:
<https://becky0713-noah-frontendapp-gehyze.streamlit.app/>

# Abbreviations and Definitions

ACS -- American Community Survey. A nationwide annual survey conducted
by the U.S. Census Bureau providing demographic, socioeconomic, and
housing estimates.

ACRIS -- Automated City Register Information System. NYC's official
system for recording property documents, including deeds, mortgages, and
transfers.

AMI -- Area Median Income. Income thresholds published by HUD and
adapted by HPD to determine housing eligibility and affordability
brackets.

BBL -- Borough Block Lot. NYC's parcel-level identifier used for tax
lots and GIS-based joins.

BIN -- Building Identification Number. Unique identifier assigned to
each building in NYC's administrative datasets.

CD -- Community District. A sub-municipal geography used by NYC for
planning and statistical reporting.

GeoJSON -- An open geospatial data format used for representing simple
geographic features and their attributes.

GEOID -- Census geographic identifier for units such as tracts, block
groups, or PUMAs.

HPD -- NYC Department of Housing Preservation and Development. Primary
city agency for affordable housing programs, data, and regulation.

HUD -- U.S. Department of Housing and Urban Development. Federal agency
responsible for AMI definitions and affordable housing policy.

LION / PAD -- NYC street centerline and address datasets used for
geocoding and spatial normalization.

NOAH -- Naturally Occurring Affordable Housing. Unsubsidized housing
units that remain affordable to low- and moderate-income households.

PLUTO -- Primary Land Use Tax Lot Output. NYC's comprehensive parcel
database combining land use, building, zoning, and assessment
attributes.

PostGIS -- Spatial extension of PostgreSQL supporting geometry storage
and geospatial queries.

REST API -- Representational State Transfer Application Programming
Interface. A standardized web service approach for exchanging structured
data.

Rent Burden -- Percentage of household income spent on gross rent.
Spending 30 percent or more indicates burden; 50 percent or more
indicates severe burden.

Three.js -- JavaScript library enabling WebGL-based 3D visualization.

311 Complaints -- NYC's public reporting system for service issues,
often used as indicators of housing quality or access.

# Introduction

Affordable housing has long been a central policy concern in New York
City, where rising rents, uneven income growth, and aging housing stock
place increasing pressure on lower- and moderate-income households.
While the city makes extensive public data available through platforms
such as NYC Open Data, ACRIS, HPD, and the U.S. Census Bureau,
researchers often need to assemble multiple sources to understand
affordability conditions across neighborhoods. Each dataset follows its
own structure, update cycle, and geographic unit, which requires
substantial preprocessing before analysis can begin.

In academic and policy literature, reliable affordability
indicators---such as rent burden, market rent patterns, income levels,
demographic characteristics, and basic housing stock attributes---are
widely recognized as essential for evaluating neighborhood-level housing
conditions. However, constructing these indicators typically involves
repetitive and time-intensive data wrangling efforts that divert
attention from substantive research questions.

## 1.1 Problem

Although relevant datasets are publicly available, they are highly
fragmented across agencies and systems. As a result, researchers must
manually locate, download, clean, and reconcile information from
numerous sources before conducting even routine analysis. This
fragmented landscape increases the cost of research, introduces
inconsistencies across projects, and limits the ability of the Urban Lab
to respond quickly to emerging policy questions.

What is lacking is a single, consolidated platform that brings together
the datasets most frequently used to study naturally occurring
affordable housing (NOAH) in NYC and presents them in a consistent,
well-documented, and interactive format. Without such a platform,
analysts repeatedly rebuild similar pipelines---an inefficient and
error-prone process that slows the production of reliable insights.

## 1.2 Approach

This project develops a unified NOAH data dashboard that integrates key
housing and socioeconomic datasets into a centralized, spatially enabled
environment. The system automates data ingestion, harmonizes geographic
identifiers, stores standardized datasets in a relational spatial
database, and provides a web-based interface for interactive
exploration. The dashboard organizes indicators into intuitive thematic
groups---such as Rent Burden, Market Rent, Income, Housing Stock, and
Demographics---mirroring the analytical structure commonly used by
policymakers and researchers.

The platform enables users to visualize spatial patterns, filter data by
geography or attributes, and export customized datasets for further
analysis. In doing so, it replaces the need for repetitive manual data
preparation with a stable, reusable, and transparent analytical
foundation.

## 1.3 Core Technology

The solution uses a modern full-stack architecture:

- **PostgreSQL/PostGIS** for spatial data storage, querying, and
  indexing

- **Python (Pandas)** for automated ETL pipelines and data
  standardization

- **REST API built with FastAPI** to serve housing project data for the
  interactive map **Streamlit with PyDeck** to provide an interactive,
  map-first user interface

- **Cloud deployment via Docker, Render, and Streamlit Cloud** for
  scalability and reliability

This technology stack was selected for its simplicity, interoperability,
and strong practical alignment with the Urban Lab's analytical
workflows.

## 1.4 Benefits

The dashboard offers several advantages to the Urban Lab:

1.  **Centralization** of commonly used NOAH-related datasets in one
    platform

2.  **Reduced research overhead** by automating data ingestion and
    standardization

3.  **Consistent geographic crosswalks** enabling reliable
    neighborhood-level comparisons

4.  **Interactive visualizations** that make patterns easier to
    interpret

5.  **Reproducible outputs** through documented schemas and API-based
    access

Together, these benefits strengthen the Lab's analytical capacity and
support faster, more transparent decision-making.

## 1.5 Research Question

This proof of concept investigates the extent to which a unified data
dashboard can reduce the time, analytical complexity, and inconsistency
typically associated with examining naturally occurring affordable
housing in New York City.

The inquiry is guided by the following subsidiary questions:\
1. To what extent can structured data pipelines streamline and
accelerate data preparation?\
2. How effectively can heterogeneous public datasets be harmonized
within a single spatial database framework?\
3. Which forms of visualization and interactivity provide the greatest
analytical value for NOAH-focused research and decision-making?

## 1.6 Contribution

This proof of concept contributes a unified and reproducible
architecture for analyzing naturally occurring affordable housing in New
York City. It consolidates multiple fragmented public datasets into a
standardized PostgreSQL/PostGIS environment, supported by a Python-based
ETL workflow and a FastAPI service layer for selected housing project
data. The project also delivers an accessible Streamlit and PyDeck
interface that enables spatial exploration of key affordability
indicators. Together, these components demonstrate a scalable,
transparent, and methodologically consistent framework that can serve as
a foundational data infrastructure for future Urban Lab research.

## 1.7 Sponsor

The project is sponsored by Professor Matthew Kwatinetz, Clinical
Assistant Professor at the NYU Urban Lab. The Lab focuses on applied
research in housing, economic development, and urban systems, and relies
heavily on integrated, high-quality datasets to support internal
research and external partnerships.

## 1.8 Importance of Project

For the Urban Lab, a consolidated NOAH dashboard directly advances its
mission of promoting data-driven urban research. By reducing the time
spent locating and preparing data, the platform enables researchers to
focus on substantive analysis and provides a durable foundation for
future modeling efforts, scenario testing, and collaborations. The
dashboard will also facilitate more consistent and transparent
evaluation of affordability challenges across NYC neighborhoods.

# Project Objectives and Metrics

## 2.1 Goal of the project

The goal of this project is to develop a unified, interactive data
dashboard for the NYU Urban Lab that consolidates publicly available
affordable housing and socioeconomic datasets relevant to naturally
occurring affordable housing (NOAH) in New York City. The dashboard aims
to provide a centralized, reproducible, and user-friendly platform for
exploring spatial patterns, generating standardized indicators, and
exporting clean datasets for further analysis.

## 2.2 Project Deliverables and Metrics

**Project Objective 1:** Data Aggregation and Standardization

Objective: Integrate multiple NYC and federal datasets into a
centralized PostgreSQL/PostGIS database with consistent schemas and
geographic identifiers.

Metric: At least five datasets successfully ingested, cleaned, and
standardized, with validated GEOID, tract, and BBL alignment.

**Project Objective 2:** Database Structure & SQL Modeling

Objective: Build a structured PostgreSQL (dataset)/PostGIS (extension of
PostgreSQL) database to support indicator generation and spatial
queries.

Metric: Relational schema with rent, income, burden, and housing supply
tables, plus SQL models for ZIP-level aggregation.

**Project Objective 3:** Backend REST API

Objective: Build a FastAPI service layer that exposes cleaned and
standardized datasets for programmatic access.

Metric: Functional API endpoints for spatial and attribute-based queries
demonstrated, with auto-generated documentation via OpenAPI.

**Project Objective 4:** Interactive Dashboard Interface

Objective: Create a Streamlit-based front-end portal with PyDeck
visualizations and indicator panels.

Metric: An MVP dashboard featuring at least two spatial layers and
interactive map exploration delivered.

**Project Objective 5:** Deployment and Documentation

Objective: Deploy the complete system---including backend, database, and
frontend---to cloud platforms with clear user documentation.

Metric: Fully deployed platform and documentation package (user manual,
API guide, and final report) submitted.

## 2.3 Project Evaluation

Project success was evaluated based on completion of the objectives and
metrics established at the beginning of the semester and agreed upon by
the sponsor. Evaluation factors included:

- Successful integration of targeted datasets into the centralized
  database

- Verified reduction in data-update time through structured ETL
  workflows

- Functionality and stability of FastAPI endpoints serving housing
  project data

- Usability and responsiveness of the Streamlit dashboard

- Accurate deployment and completeness of documentation

These criteria align with the final acceptance requirements approved by
the project sponsor.

# Alternate Solutions Evaluated

Several alternative tools and architectures were evaluated before
selecting the final implementation stack. These alternatives represented
commonly used options in urban analytics and civic-tech applications but
were ultimately not chosen due to development constraints, complexity,
or limited alignment with project goals.

## 3.1 Solution Evaluation Criteria

### **3.1.1 React Frontend with Mapbox GL JS or Leaflet**

A full custom frontend using React paired with Mapbox GL or Leaflet was
considered.\
**Advantages:**

- High flexibility in UI/UX design

- Widely used for production-grade mapping applications

- Strong ecosystem for custom layers and animations

**Limitations:**

- Requires substantial JavaScript development time

- Higher maintenance overhead

- Not aligned with the capstone timeline for solo development

- Requires parallel frontend--backend integration work

Because the goal was to rapidly prototype a functional,
research-oriented dashboard rather than build a fully custom web app,
this option was not selected.

### **3.1.2 Flask Instead of FastAPI for Backend Services**

Flask was initially considered because of its simplicity and wide
adoption.\
**Advantages:**

- Lightweight and flexible

- Large community and documentation

**Limitations:**

- Lacks built-in async support

- No automatic schema validation

- No automatic OpenAPI documentation

Given the need for clean, documented, and scalable REST endpoints,
**FastAPI offered superior performance and easier maintainability**,
leading to its selection.

### **3.1.3 GeoPandas for Spatial Processing**

GeoPandas was evaluated as an ETL option for directly manipulating
geometries in Python.\
**Advantages:**

- Intuitive geospatial data manipulation

- Good for exploratory analysis

**Limitations:**

- Slow with large NYC-scale datasets

- Less efficient than pushing geometry handling to PostGIS

- Adds unnecessary overhead to ETL pipeline

Because all spatial operations could be delegated to the PostGIS
backend, GeoPandas was not adopted.

### **3.1.4 BI Tools Such as Apache Superset or Tableau**

Superset and Tableau were briefly considered as alternatives for
visualization.\
**Advantages:**

- Easy dashboard creation

- Built-in filtering and exploration

- No need to build low-level UI

**Limitations:**

- Limited geospatial customization

- Less control over indicator logic

- Not ideal for API-driven or programmatically reproducible workflows

- Harder to integrate with automated ETL pipelines

Since the dashboard required custom, map-first exploration with
consistent schema control, BI tools were not chosen.

## 3.2 Solution Evaluation Criteria

To evaluate and compare options, several criteria were established at
the beginning of the project:

a.  **Time Feasibility**\
    Given the semester timeline, the solution needed to enable rapid
    prototyping while maintaining technical rigor.

b.  **Technical Simplicity and Maintainability**\
    Urban Lab researchers should be able to extend or maintain the
    system with minimal onboarding.

c.  **Data Reproducibility**\
    The platform needed to support standardized schemas, geographic
    keys, and consistent ETL logic.

d.  **Scalability and Transparency**\
    The solution should support future datasets and analytical modules
    without major redesign.

e.  **User Accessibility**\
    The interface should be easily accessible to researchers without
    requiring front-end development experience.

## 3.3 Selection Rationale

After evaluating alternatives, the chosen
architecture---PostgreSQL/PostGIS + Python (Pandas) + FastAPI +
Streamlit/PyDeck + Render/Streamlit Cloud---was selected because it best
met the project's goals:

- **Fast prototyping** with Streamlit allowed all focus to be placed on
  data integrity and spatial analysis rather than UI engineering.

- **FastAPI** provided clean, automatically documented endpoints and
  strong performance.

- **PostGIS** handled all spatial joins and indexing efficiently,
  reducing ETL code complexity.

- **Pandas-based ETL** workflows minimized overhead and kept the data
  transformation process clear and reproducible.

- **PyDeck** offered robust geospatial visualization without requiring
  JavaScript.

- **Docker-based deployment** for the backend and cloud hosting for both
  services ensured reproducibility and simplified environment setup.

> Collectively, these tools aligned with the Urban Lab's need for a
> transparent, extensible, and data-first platform while remaining
> achievable within the capstone timeline.

# Literature Survey

## 4.1 Introduction

This literature review supports a focused proof of concept for the
**NOAH (Naturally Occurring Affordable Housing) Dashboard for NYC**. The
tool's primary goal is clear, trustworthy presentation of affordable
housing data with lightweight, interpretable analysis, no predictive
modeling or complex welfare simulations. Indicators are organized around
six practical analytical dimensions that mirror the way housing
stakeholders already discuss needs and trade-offs. These dimensions
include Rent Burden, Market Rent, Income, Housing Stock, Demographics,
and Access and Complaint Data.

The review synthesizes literature that (a) establishes why these six
dimensions matter for affordability monitoring, (b) documents common
data and crosswalk challenges in NYC, and (c) supports a simple,
standards-based stack (PostgreSQL, Python ETL, and React) to publish
maps, tables, and downloadable datasets. Health and welfare findings
appear only as background motivation for why rent-burden and access
indicators are policy-relevant, not as features the tool must compute.
The chapter is organized thematically into the following sections:
Industry, Problem, Proposed Solution, Technology, Use Cases, and
Conclusion. For grounding, this chapter draws on Meltzer and Schwartz
(2016) for NYC rent‑burden measurement; Boeing and Waddell (2017) for
listing‑based asking‑rent indicators; Ambrose, Coulson, and Yoshida
(2015) for quality‑adjusted rent indexing; Sieg and Yoon (2019) for
access frictions; Schwartz (2019) for NYC policy context; Zapatka, de
Castro, and Galvão (2023) for rent stabilization; Desmond and Wilmers
(2019) for price setting in low‑income markets; and Fields and Uffer
(2014) for financialization dynamics.

## 4.2 The Industry

The U.S. rental market has experienced persistent affordability stress,
with cost‑burden rates particularly acute in large metros such as New
York City. Across major cities, supply constraints, aging housing stock,
and uneven income growth have increased the share of renters spending at
least thirty percent of income on housing (Colburn & Allen, 2018). In
New York City, measured rent‑burden disparities align with neighborhood
income patterns and with differences in access to opportunities (Meltzer
& Schwartz, 2016). A second strand of work shows that price signals from
listings illuminate local dynamics when interpreted carefully (Boeing &
Waddell, 2017), and that quality‑adjusted rent indexing helps separate
composition from true price change (Ambrose, Coulson, & Yoshida, 2015).
Allocation institutions also matter; queueing and search frictions are
first‑order features of how households obtain regulated or subsidized
units in the city (Sieg & Yoon, 2019). Finally, policy context shapes
observed outcomes, including the role of rent stabilization and who
benefits from it (Schwartz, 2019; Zapatka, de Castro, & Galvão, 2023).
Concurrently, cities have embraced urban informatics, the systematic use
of open administrative and survey data to inform planning, although
platforms vary in usability and interoperability (Schwartz, 2019). The
literature underscores that integrated, standards-based data portals can
reduce transaction costs for policy analysis and stakeholder engagement
in housing.

A second stream of industry literature tracks housing production,
preservation, and naturally occurring affordable housing, defined as
unsubsidized units affordable to lower‑ and moderate‑income households.
In New York City, reviews of programs and policy changes document how
preservation tools, code enforcement, and acquisition can stabilize
affordability in gentrifying areas when guided by timely parcel‑level
information and inter‑agency coordination (Schwartz, 2019). Comparative
work further cautions that financialization pressures can reshape rental
markets and the composition of stock (Fields & Uffer, 2014). For NYC,
administrative datasets such as HPD, DOB, and DOF or ACRIS, as well as
federal sources such as the ACS, are foundational yet siloed. This
complicates efforts to monitor loss of affordability, track capital
needs, and align subsidy programs with neighborhood trajectories. For
NYC, administrative datasets such as HPD, DOB, and DOF or ACRIS, as well
as federal sources such as the ACS, are foundational yet siloed. This
complicates efforts to monitor loss of affordability, track capital
needs, and align subsidy programs with neighborhood trajectories.

Finally, industry research on climate and resilience links housing
vulnerability to flood risk, heat exposure, and building energy
performance. Integrating resilience layers with affordability metrics
enables more holistic risk-benefit assessment for investments and tenant
protection policies. Actionable platforms must support spatio-temporal
analysis, such as changes in flood maps, capital improvements, or 311
complaints over time, while remaining interpretable for nontechnical
stakeholders. These demands shape the requirements for the NOAH
Dashboard's indicator design and map interactivity.

## 4.3 The Problem

Despite a wealth of NYC open data, fragmentation, inconsistent schemas,
and limited crosswalks impede synthesis across housing, demographics,
resilience, and service-access indicators. Researchers frequently
duplicate ETL work, while versioning and refresh cadences differ by
source, reducing reproducibility. Critical measures such as rent burden,
code violations, and foreclosure signals exist at mismatched
geographies, including tract, PUMA, community district, and BIN or BBL,
as well as at different time scales, complicating comparisons or
longitudinal analysis. Visualization tools often hard-code layers
without standardized metadata, hindering discoverability and quality
control. Consequently, policy and academic users face high transaction
costs to assemble decision-ready views for neighborhoods, leading to
delays and inconsistent evidence bases.

## 4.4 Proposed Solution

The proposed solution is an open, modular, standards-oriented dashboard
that ingests authoritative public data via automated pipelines,
harmonizes geographies with robust crosswalks (for example, BBL to tract
to community district), stores spatial data in PostgreSQL or PostGIS
with provenance and versioning, exposes documented REST APIs for
external reuse, and renders interactive visualizations using Mapbox GL
or Leaflet and Three.js with multiple layers and time controls. Prior
work shows that such architectures improve data reuse, transparency, and
policy uptake when coupled with clear metadata and user-centered design.
Relative to current NYC portals, the NOAH Dashboard's contribution is a
unified, NOAH-focused indicator model paired with reproducible pipelines
and open services, enabling academics and agencies to share a common
analytical foundation.

## 4.5 The Technology

A relational spatial design in PostgreSQL supports geometry types,
parcel polygons, and building footprints, along with indices for
efficient geospatial queries. Normalized core tables, including parcels,
buildings, rent burden, complaints, sales, and permits, link through
durable keys such as BBL and BIN and maintain provenance columns,
including source ID, snapshot date, and transform hash. Materialized
views precompute common joins, such as parcel to tract to district, and
indicator summaries to accelerate map rendering.

ETL is implemented in Python with Pandas, orchestrated by a lightweight
scheduler such as cron or GitHub Actions or a workflow tool such as
Prefect. Crosswalks, including Census GEOIDs, NYC PLUTO, LION, and PAD,
are versioned to ensure reproducibility when boundaries change. Metadata
follows a simplified Frictionless Data pattern using resource
descriptors, schemas, and data dictionaries. APIs adhere to REST
conventions with OpenAPI documentation, rate limits, and token
authentication. Geospatial endpoints return GeoJSON or PMTiles for
efficient web maps.

The front end uses React with Mapbox GL or Leaflet for vector-tile
rendering and a Three.js layer for 3D context, such as extruded
buildings and energy or age shading. The user interface emphasizes
map-first exploration with side-panel legends, filters, and time
sliders. Accessibility and performance are addressed through progressive
loading, tile caching, and WebGL instancing. Empirical studies report
that multiscale visualization with clear legends and uncertainty cues
improves interpretability for nonexperts, especially when paired with
scenario narratives and export functions.

Cloud deployment on AWS or GCP hosts the API and tile server. Database
backups and row-level security protect restricted tables if needed.
Observability includes structured logs and metrics such as latency,
error rates, and ETL freshness. Versioned releases and a change log
support academic citation of specific data snapshots.

## 4.6 Use Cases

**Use Case 1: Neighborhood affordability snapshot.** Users choose a
geography, such as a tract or community district, and view a concise
panel showing rent-burden distribution, median market rent (asking),
income percentiles compared with AMI, stock age or tenure mix, and a
rolling count of 311 heat or hot-water complaints. This consolidates
scattered sources into a single screen without advanced modeling.

**Use Case 2: Simple trend and comparison.** Users toggle a time slider
to see market-rent trends and rent-burden changes and to compare two
neighborhoods side by side. The portal provides clear caveats, including
asking rent versus signed lease, geographic definitions, and data
vintages.

**Use Case 3: Quick download for analysis.** With one click, users
export a tidy CSV or GeoJSON file for any selected area, including
standardized keys such as GEOID and BBL or BIN, so analysts can join to
external models.

## 4.7 Conclusion

The literature supports a lean, standards-based portal that harmonizes
NYC housing data across the six dimensions above and improves
transparency with minimal computational burden. Rather than forecasting
outcomes, the dashboard's value proposition is to reduce transaction
costs for routine questions such as "What are rent-burden levels here?"
"How do asking rents compare across neighborhoods?" and "What stock
characteristics or complaint patterns coincide with higher burden?"
while documenting data lineage and caveats. This scoped approach aligns
with evidence that interoperability, clear metadata, and simple
visualizations increase uptake by policy and community users. The
chapter therefore justifies proceeding with a lightweight MVP centered
on presentation, standard joins, and basic descriptive statistics,
leaving advanced analytics to external tools that can reuse the portal's
clean outputs.

From these examples and existing literature supporting this application,
we conclude that a standards-based, open, and modular spatial data
portal can substantially reduce the time and expertise required to
assemble decision-ready NOAH insights in NYC. Specifically examining the
intersections of affordability, stock condition, service access, and
resilience, the literature supports harmonized geographies, reproducible
ETL, and programmable APIs as enabling conditions for rigorous
evaluation and collaboration. Most of the literature reviewed concluded
that transparency, interoperability, and user-centered visualization
increase uptake of evidence in policy and research, outcomes aligned
with the NOAH Dashboard's goals. The proposed stack (PostgreSQL,
PostGIS, and React or Mapbox or Three.js) is technically mature, widely
documented, and already proven in adjacent civic-tech deployments,
suggesting low implementation risk and high reusability. The chapter
therefore substantiates proceeding with the technology trial and
highlights where careful attention to governance, metadata, and
crosswalk versioning will determine success.

# Approach and Methodology

## 5.1 Problem Statement and Research Question

Despite the availability of extensive open data resources in New York
City, information relevant to naturally occurring affordable housing
(NOAH) remains fragmented across multiple agencies, platforms, and
geographic definitions. Researchers must spend considerable effort
locating, downloading, cleaning, and harmonizing datasets before
performing any substantive analysis. This fragmentation reduces
analytical efficiency and limits the Urban Lab's ability to conduct
timely, reproducible, and data-driven evaluations of neighborhood
affordability.

The overarching research question guiding this project is therefore:\
**How can a unified data dashboard reduce the time, complexity, and
inconsistency associated with analyzing naturally occurring affordable
housing in New York City?**\
Supporting questions include how automated ETL workflows compare to
manual processes, whether tract- and ZIP-level indicators can be
harmonized into a consistent spatial framework, and how a lightweight
visualization interface can improve accessibility for nontechnical
researchers.

## 5.2 Proof of Concept Approach

The goal of this proof of concept is to design a unified, reproducible,
and spatially coherent data infrastructure that brings together the core
indicators needed to analyze naturally occurring affordable housing
(NOAH) in New York City. The project follows a structured approach that
integrates data acquisition, automated cleaning, spatial harmonization,
database engineering, API development, and user-facing visualization.

The methodology is grounded in a full-stack architecture consisting of:

- PostgreSQL/PostGIS for centralized spatial data storage

- Python and Pandas for ETL and schema standardization

- FastAPI for programmatic access to selected housing project data

- Streamlit and PyDeck for map-based dashboard visualization

- Docker, Render, and Streamlit Cloud for deployment

The emphasis is on transparency, reproducibility, and alignment with
Urban Lab's workflow, enabling researchers to work with clean,
harmonized datasets while minimizing repetitive data-processing
effort.**\**

## 5.3 Technology Trial Plan

[]{#_Toc215500436 .anchor}To evaluate the effectiveness of structured
data-processing workflows, a technology trial was designed following the
framework outlined in Appendix B. The primary objective of the trial was
to assess how a scripted ETL workflow compares to fully manual
processing in terms of consistency and repeatability when integrating
ACS, StreetEasy, and affordable-housing datasets into a unified
PostgreSQL/PostGIS database.

In the implemented workflow, Python and Pandas were used to script
portions of the cleaning and standardization process, while other
tasks---such as downloading source files and uploading cleaned
tables---remained manual. This structured workflow was compared
conceptually to the previous practice of handling each dataset entirely
by hand. For each dataset, the project recorded processing steps,
identified common failure points, and documented sources of schema or
formatting inconsistency. Independent variables include the type of
processing workflow (fully manual vs. partially scripted), while
dependent observations include processing effort, risk of schema
mismatch, and geographic completeness of resulting tables.

Because a fully automated pipeline was not implemented during this
capstone, the technology trial focuses on documenting process
improvements achieved through scripting, identifying where automation
would yield the greatest benefits, and establishing the baseline
requirements for future automated ETL development. The implications of
these observations are discussed in the Results chapter.

## 5.4 Population/Data

This project uses five primary categories of datasets, all of which were
stored in PostgreSQL/PostGIS and standardized to ZIP-code geography for
dashboard visualization. Together, these datasets represent the relevant
NYC population for evaluating affordability conditions: households from
ACS 5-Year Estimates, residential units represented in PLUTO, and rental
listings collected from StreetEasy.

### **5.4.1 Rent Burden (ACS 5-Year Estimates)**

Rent burden indicators were derived from:

- **B25070** -- Gross rent as a percentage of household income

- **B25074** -- Household income by gross rent category

These tract-level variables were processed into:

- share of households paying \>30 percent of income on rent

- share of households paying \>50 percent of income on rent

The database tables rent_burden, rent_income_distribution, and
zip_rent_burden_ny reflect the output of this ETL pipeline.

### **5.4.2 Income (ACS 5-Year Estimates)**

Median household income was obtained from:

- **B19013** -- Median Household Income

This dataset supports the zip_median_income and zip_rent_income_ratio
tables. Income measures were also harmonized to ZIP-code geography using
the same tract-to-ZIP crosswalk applied for rent burden.

### **5.4.3 Market Rent (StreetEasy)**

Market rent indicators were constructed **exclusively from StreetEasy**,
which provides monthly rental listing data for New York City.

Rather than aggregating all listings together, median asking rents were
computed **separately for each unit type**, including:

- Studio

- One-bedroom

- Two-bedroom

- Three-bedroom or larger

Monthly medians were then aggregated to **ZIP-code level** to create the
zip_median_rent table, which serves as the market rent indicator for the
dashboard.\
No Zillow or ACS rent variables were used.

### **5.4.4 Demographics (ACS 5-Year Estimates)**

Demographic context was derived from the following Census tables:

- **B01001** -- Age distribution

- **B03002** -- Race and ethnicity

- **B11016** -- Household size

These indicators were stored at the tract level and converted into
ZIP-level demographic summaries for dashboard filtering and comparison.

### **5.4.5 Geographic Data and Crosswalks**

The project combines tract-level ACS data with ZIP-level rent
indicators. To resolve this mismatch, an externally sourced
**tract-to-ZIP weighted crosswalk** was used. The crosswalk includes
population-based allocation factors, enabling accurate transformation of
tract-based indicators into ZIP-code equivalents.

Spatial layers used in the dashboard include:

- **ZIP code geometry** (zip_shapes, zip_shapes_geojson)

- **Census tract boundaries**

- **Tract-to-ZIP crosswalk** (zip_tract_crosswalk)

These geometric and relational datasets form the foundation of all
spatial joins executed in the ETL workflow.

## 5.5 Procedures

The project followed a structured methodology involving spatial
harmonization, automated ETL processing, database integration, API
development, visualization engineering, and cloud deployment. The
procedures below summarize the full workflow.

### **5.5.1 Data Harmonization via Crosswalks**

A core requirement of the project was to produce indicators at a
consistent geographic level for visualization and analysis. Because ACS
variables are published at the **tract level**, while market rent is
available only at the **ZIP level**, harmonization was necessary.

The harmonization process included:

a.  **Joining ACS tract data with tract-to-ZIP crosswalk**

b.  **Multiplying tract-level values by crosswalk allocation factors**

c.  **Aggregating weighted values to ZIP code**

d.  **Validating the resulting ZIP indicators for completeness**

e.  **Storing results as cleaned ZIP-level tables**

This methodology ensures that rent burden, income, and demographic
indicators are comparable with StreetEasy ZIP-level rent metrics.

### **5.5.2 ETL Workflow (Python + Pandas + SQL)**

The ETL pipeline was implemented in Python using Pandas for data
transformation and SQLAlchemy/psycopg for database insertion. The
workflow included:

1.  API calls to ACS and StreetEasy

2.  Parsing and cleaning raw JSON/CSV inputs

3.  Standardizing variable names, data types, and GEOIDs

4.  Applying geographic crosswalk transformations

5.  Computing derived indicators (burden shares, ratios, medians)

6.  Writing cleaned outputs to PostgreSQL tables

7.  Logging ETL run times for evaluation in the Technology Trial

### **5.5.3 Database Schema (PostgreSQL/PostGIS)**

All processed datasets were stored in the public schema of the
project\'s PostgreSQL database. Key tables include:

- **rent_burden** -- tract-level rent burden metrics

- **rent_income_distribution** -- ACS rent-income cross-tabs

- **zip_rent_burden_ny** -- ZIP-level burden indicators

- **zip_median_income** -- median household income

- **zip_median_rent** -- StreetEasy median rents by unit type

- **zip_rent_income_ratio** -- derived affordability ratio

- **zip_shapes / zip_shapes_geojson** -- ZIP geometry

- **zip_tract_crosswalk** -- geographic harmonization reference

PostGIS geometry columns were indexed using GIST to enable efficient
selection and rendering of spatial features.

### **5.5.4 API Architecture (FastAPI)**

A FastAPI backend was deployed to allow programmatic access to cleaned
datasets.\
The API provides:

- JSON and GeoJSON outputs

- Parameterized filters by ZIP code, geography, or indicator

- Automatic OpenAPI documentation

- Schema validation via Pydantic

The API enables both the dashboard and external analysts to retrieve
standardized, reproducible slices of the database.

### **5.5.5 Dashboard Visualization (Streamlit + PyDeck)**

The user interface was implemented in Streamlit, prioritizing
accessibility and rapid development.\
PyDeck was used for interactive 2D and 3D map visualizations, allowing
users to:

- view ZIP-level indicators

- toggle between rent burden, median rent, income, and demographic
  layers

- zoom, pan, and filter geographies

- inspect values through interactive tooltips

Streamlit's simplicity ensures that researchers can extend the interface
without needing frontend engineering expertise.

### **5.5.6 Deployment (Render + Streamlit Cloud + Docker)**

Deployment architecture includes:

- **Render** for hosting the FastAPI backend

- **Streamlit Cloud** for hosting the dashboard

- **Docker** for containerizing backend dependencies and ensuring
  reproducibility

This cloud-based deployment model eliminates local configuration burdens
and ensures persistent, publicly accessible endpoints for demonstration.

### **5.5.7 Technology Trial Summary**

The Technology Trial examined whether automated ETL significantly
reduces processing time compared with manual workflows.\
Following the design in the Technology Trial Plan ():

- Automated ETL achieved a measurable reduction in update time

- Error rates decreased due to standardized schema enforcement

- Trial results validated the decision to adopt automation as the system
  default

The trial confirms that automation meaningfully improves data freshness,
reliability, and reproducibility for Urban Lab workflows.

## 5.6 Organizational Change Plan

The adoption of the NOAH dashboard introduces operational changes for
the Urban Lab, which has historically relied on manual data collection
and ad hoc analytical workflows. Organizational barriers may include
resistance from staff accustomed to scattered datasets, limited
familiarity with structured ETL processes, and uneven technical
competency across team members. These factors may hinder adoption of a
unified platform unless clear standards, documentation, and training
processes are established.

To address these challenges, the change strategy emphasizes building a
shared data culture grounded in transparency, reproducibility, and
standardized procedures. The dashboard's structured ETL workflow,
documented schema, and centralized database reduce ambiguity and promote
consistent analytical practices. Training sessions, open Q&A channels,
and step-by-step documentation will support the transition, while
iterative feedback loops ensure that the system continues to evolve with
user needs. A more complete organizational change management plan is
provided in Appendix G.

# Results

## 6.1 Data Processing

The project involved extensive cleaning, transformation, and
harmonization of multiple datasets prior to database integration and
dashboard visualization. Beyond crosswalk-based geographic alignment,
several foundational data-cleaning operations were required to ensure
dataset integrity.

### **6.1.1 Data Acquisition and Initial Cleaning**

For each dataset (ACS tables, StreetEasy rents, PLUTO, geographic
layers):

- **Removed non-New York City observations** to ensure that only the
  five boroughs remained in scope.

- **Dropped rows with missing or null values** for key indicators (rent,
  income, burden counts).

- **Standardized ZIP codes and GEOIDs** by padding leading zeros and
  converting all identifiers to string format.

- **Normalized variable names and data types** to maintain consistency
  across datasets.

- **Validated geometries** using PostGIS functions (ST_IsValid,
  ST_MakeValid) to ensure the spatial layers could be rendered without
  error.

### **6.1.2 Database Schema Creation**

Using SQL, a structured schema was designed in PostgreSQL/PostGIS to
store:

- ZIP-level indicators

- Tract-level ACS tables

- Market rent tables

- Geometries (ZIP polygons, tract polygons)

- Crosswalk mapping tables

Custom SQL tables were created for each indicator category using
standardized column names and appropriate data types. GIST indexes were
added to geometry columns to optimize spatial queries.

### **6.1.3 ETL Processing Using Python + SQL**

For each dataset:

- Parsed raw CSV/JSON using Pandas

- Cleaned column names, removed duplicates, enforced naming conventions

- Applied tract-to-ZIP weighted allocation for ACS datasets

- Aggregated monthly StreetEasy rental listings **separately by bedroom
  type**

- Calculated derived indicators (burden shares, median rent by unit
  type, income--rent ratios)

- Uploaded the cleaned tables to the cloud PostgreSQL database using
  SQLAlchemy/psycopg2

- Verified table row counts and key constraints after upload

### **6.1.4 Database-Level Transformations**

Within PostgreSQL, additional transformations ensured data consistency:

- Enforced primary keys on ZIP codes

- Performed joins between geometric layers and indicator tables

- Computed borough-level aggregates for rent burden analysis

- Ensured each ZIP polygon had a complete set of indicators for
  visualization

These steps ensured that all layers in the dashboard were clean,
harmonized, and aligned to ZIP geography.

## 6.2 Outcomes

### 6.2.1 Page 1 - App page

![Introduction of App
Page](media/image1.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="5.828525809273841in" height="3.949821741032371in"}

**A. Main Navigation Panel**

This is the primary navigation panel of the website. It contains three
tabs, with **"app"** being the default landing page when the website
opens.

**B. Project Filters -- Project Status**

The first filter allows users to narrow results by **project status**.\
You can choose between **"In Progress"** or **"Completed"** projects.

**C. Low-Income Unit Filter**

This checkbox enables users to filter the map to show **only projects
that include low-income units**.

**D. Bedroom-Type Filter**

Users can filter projects based on the **types of units available**
(e.g., Studio, 1 Bedroom, 2 Bedroom, 3+ Bedroom).\
This is particularly useful for users who want to see where larger
family-sized units (such as 3+ bedrooms) are available.

**E. Location Filters**

This section allows users to filter by **borough, ZIP code, or street
name**, helping renters or researchers quickly focus on a specific
neighborhood or area within NYC.

**F. Interactive Map**

The main interactive map visualizes all affordable housing projects.\
When hovering over any point (each dot represents an individual
affordable housing project), a detailed info panel appears showing
additional attributes of that project.\
(See the next screenshot for the hover details.)

![Interactive
Map](media/image2.png){alt="A screenshot of a map AI-generated content may be incorrect."
width="5.877201443569554in" height="3.709041994750656in"}

As shown in the figure, when the cursor hovers over a dot on the map, a
tooltip appears displaying the following information:

- **Project ID**

- **Borough**

- **Postcode**

- **Building completion date**

- **Types and counts of income-restricted units**

- **Types and counts of bedroom units**

- **Total number of rental units**

These details cover most of the essential information about each
project.\
If users wish to view **more comprehensive information**, they can
scroll down to the **"Search by Project ID"** section and enter the
desired project ID to retrieve the full project profile.

For example, if we search for the project with ID **53392**, the
dashboard will display the following information, as shown in the next
screenshot:

![Result 1 of "Search by Project
ID"](media/image3.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="6.5in" height="4.408333333333333in"}

![Result 2 of "Search by Project
ID"](media/image4.png){alt="A screenshot of a document AI-generated content may be incorrect."
width="6.5in" height="3.7006944444444443in"}

![Data Download
Function](media/image5.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="6.5in" height="0.7021544181977253in"}

Regardless of whether a user performs a project-specific search, all
data related to affordable housing displayed on this page can be
downloaded directly using the **"Download"** section. This allows users
to export the full dataset for further analysis or offline use.

### 6.2.2 Page 2 - Analysis Page

**A. Value Lookup**

Users can select a **Bedroom Type**, enter a **ZIP code**, and choose
the **indicator** they want to view, including three options \-- median
income, median rent, or rent burden.

Note that the **Bedroom Type** filter applies **only to median rent**,
since rental prices vary by unit type. For median income and rent
burden, users do not need to select a bedroom type to perform the
lookup.

![Analysis Dashboard, Value
lookup](media/image6.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="6.5in" height="2.3375in"}

### B. **Most Critical Areas**

Users can specify their criteria through a set of dropdown menus:

- **Metric Type** (e.g., *Lowest Median Income* or *Highest Rent
  Burden*)

- **Borough** (or *All NYC*)

- **Number of Results** --- this determines how many of the most
  critical ZIP codes the user wants to view

After running the search, the module returns a list of ZIP codes that
meet the selected criteria, along with their corresponding indicator
values.

As shown in figure 6-8, users may also choose to display only the **top
three** results.\
Additionally, when hovering over the **three dots** in the upper-left
corner of the table, several options appear. These include:

- **Filter** (apply additional conditions)

- **Download** (export the table data)

- **Search** (locate specific entries within the table)

- **Enlarge** (expand the table for better visibility)

![Analysis Dashboard, Most Critical Areas,
Outlook](media/image7.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="6.5in" height="4.197222222222222in"}

![Analysis Dashboard, Most Critical Areas, Table
Operation](media/image8.png){alt="A screenshot of a computer AI-generated content may be incorrect."
width="6.5in" height="3.2631944444444443in"}

### C. **Visualization Maps**

Users can choose to view any of the following map layers:

- **Median Rent**

- **Median Income**

- **Rent Burden**

Each map provides an interactive, ZIP-code--level visualization to help
users quickly identify geographic patterns and affordability conditions
across New York City.

**Map 1: Median Rent Map**\
Because rent levels vary significantly by **bedroom type**, the
selection made in **Module 1** (Value Lookup) directly determines how
this map is displayed. A bedroom type **must** be selected for the
median rent map to load properly.

In the example shown, the selected unit type is **Studio**. The map
displays **54 ZIP codes** that contain studio rental data. On the color
scale, **red indicates higher median rent**, while **green indicates
lower rent** levels. When the user hovers over any ZIP code on the map,
a tooltip appears showing the **exact median rent value** and the
**corresponding area name**.

![Median Rent
Map](media/image9.png){alt="A map of the world AI-generated content may be incorrect."
width="6.5in" height="3.8408737970253717in"}

**\**

**Map 2: Median Income Map**\
Unlike the median rent map, the **median income map** is **not
affected** by the bedroom type selection and will display normally
regardless of the chosen unit type. In this visualization, **red
represents lower median income**, while **green represents higher
income** levels across ZIP codes. When the user hovers over a specific
ZIP code on the map, a tooltip appears showing the **exact median income
value** and the **corresponding area name**.

![Median Income
Map](media/image10.png){alt="A map of the united states AI-generated content may be incorrect."
width="6.5in" height="4.340277777777778in"}

**\**

**Map 3: Rent Burden Map**\
Similar to the median income map, the **rent burden map** is **not
affected** by the bedroom type selection and will display normally
regardless of the chosen unit type. ZIP codes where **30%--50% of
households** are rent-burdened appear in **yellow**, while areas where
**more than 50%** of households are rent-burdened appear in **red**. The
color intensity increases as the rent burden percentage rises. When the
user hovers over a ZIP code, a tooltip displays the **exact rent burden
value** and the **corresponding area name**.

![Rent Burden
Map](media/image11.png){alt="A map of the world AI-generated content may be incorrect."
width="6.5in" height="4.000694444444444in"}

**\**

### 6.2.3 Page 3 - Rent Burden page

The **third module** on the Rent Burden page provides a **macroscopic
analysis** of rent burden patterns across New York City.

![Rent Burden Dashboard, Summary
Statistics](media/image12.png){alt="A screenshot of a screen AI-generated content may be incorrect."
width="5.898182414698162in" height="2.1317891513560805in"}

A.  **Borough-Level Rent Burden Data Summary**\
    Figure 6-12 displays the **average rent burden rate for each
    borough**, accompanied by a numerical summary of the **rent burden
    thresholds** (e.g., \>30%, \>50%). These values help users
    understand the differences in affordability challenges across
    boroughs. The underlying borough-level dataset can also be
    downloaded directly by users.

![Rent Burden Dashboard, Rent Burden
Histogram](media/image13.png){alt="A graph of blue and red squares AI-generated content may be incorrect."
width="5.980597112860893in" height="3.2893285214348205in"}

B.  **Rent Burden Histogram**\
    The second chart presents these rent burden values in the form of a
    **histogram**, providing a more intuitive view of the overall
    distribution. This allows users to see how rent burden is spread
    across ZIP codes and where the most common burden levels fall.

![Income Rent Burden Distribution, All
Borough](media/image14.png){alt="A screenshot of a graph AI-generated content may be incorrect."
width="4.8828947944007in" height="3.607396106736658in"}

![Income Rent Burden Distribution,
Manhattan](media/image15.png){alt="A screenshot of a computer screen AI-generated content may be incorrect."
width="4.908579396325459in" height="3.6421030183727034in"}

C.  **Income--Rent Burden Distribution**\
    Figures 6-15 (the whole New York city) and 6-16 (Manhattan Borough)
    display the **distribution of rent burden across different income
    ranges**. Users can filter the chart by borough to focus on specific
    areas. Rent burden levels are represented as a **stacked bar chart**
    with distinct colors corresponding to different burden percentages,
    making it easier to compare affordability across income groups.

## 6.3 Findings

The integrated datasets revealed several notable spatial and
socioeconomic patterns across New York City.

**A. NYC Rent Burden is High Almost Everywhere**

Analysis shows that **nearly all ZIP codes in NYC exceed the 30% rent
burden threshold**, meaning that most NYC households are rent-burdened
by federal standards. This indicates citywide affordability pressure,
not isolated to a few low-income areas.

**B. Higher-Income ZIP Codes Appear to Have Higher Rent Burden---Why?**

Some affluent ZIP codes surprisingly show **rent burden rates comparable
to or higher than low-income areas**.\
This may occur because:

- High-income ZIPs also have **extremely high rents**, raising the
  proportion of households spending \>30% on rent even if incomes are
  high.

- Wealthier neighborhoods often have **large renter populations of young
  professionals**, whose high rent-to-income ratios reflect lifestyle
  decisions rather than poverty.

- The ACS rent burden metric is based on **all renter households**, not
  only long-term residents. Newcomers often pay premium rents.

Thus, "high burden" in wealthy areas reflects **market competitiveness
and spending choices**, not financial hardship.

**C. Rent Prices Exhibit Strong Geographic Divides**

- **Manhattan (except some pockets of Upper Manhattan) and certain parts
  of Brooklyn** show the highest median rents, especially in ZIP codes
  such as 10014, 10011, 11201, and 11215.

- **The Bronx and most of Queens** show substantially lower rents across
  all bedroom types.\
  This reflects both income disparities and historical development
  patterns.

**D. Affordable Housing Supply is Uneven**

Using the project-level supply map:

- **Midtown Manhattan has very few affordable housing projects**,
  compared to Upper Manhattan and Lower Manhattan.

- Brooklyn displays a mixed pattern, with concentrations of affordable
  units in Central Brooklyn but limited supply in high-cost coastal
  areas.

- The Bronx has the largest number of affordable housing projects
  relative to land area.

**E. Rent-to-Income (Rent Burden) Ratios Reflect Combined Market
Pressure**

Even in areas with moderate rents, low incomes create affordability
strain.\
Similarly, high-income neighborhoods still show ratios above 0.30 due to
extremely high asking rents.

**F. Income and Rent Maps Align but Also Reveal Outliers**

In some ZIP codes:

- **High income + high rent = "expected" equilibrium**

- **Low income + low rent = "expected" equilibrium**

- **High income + high burden OR low income + moderate rent =
  "unexpected outliers"**\
  These outliers represent neighborhoods where additional policy focus
  may be needed.

## 6.4 Summary Statistics

High-level summary statistics derived from the final processed datasets
include:

  --------------------------------------------------------------------
  **Indicator**        **Range**      **Interpretation**
  -------------------- -------------- --------------------------------
  Median Rent (Studio) \$2,050 --     Strong spatial variation;
                       \$6,200        Manhattan highest

  Median Household     \$2500 --      Wide socioeconomic disparities
  Income               \$250,000+     

  Rent Burden (\>30%)  6% -- 86%      Burden highest in lower-income
                                      areas
  --------------------------------------------------------------------

To complement the dashboard visualizations, the processed datasets
reveal several notable patterns across New York City's ZIP codes. Studio
median rents show substantial geographic dispersion, ranging from
approximately \$2,050 in lower-cost neighborhoods to more than \$6,200
in high-demand Manhattan areas, illustrating the sharp spatial gradient
of rental market pressures. Median household income exhibits an even
wider spread, from roughly \$25,000 in lower-income communities to more
than \$250,000 in affluent areas, reflecting persistent socioeconomic
inequality across the city's neighborhoods. Rent burden also varies
significantly, with the share of households paying more than 30 percent
of income on rent ranging from 6 percent in higher-income ZIP codes to
more than 80 percent in some of the lowest-income areas. These
statistics indicate that affordability challenges are not limited to any
single borough or demographic group but instead reflect a complex
interaction between market rent levels, local economic conditions, and
household income distribution. Together, these patterns reinforce the
need for consistent, spatially harmonized indicators to support
comparative analysis and policy evaluation across the city.

## 6.5 Implications

### **6.5.1 Practical Implications**

For policymakers, researchers, and housing agencies, the dashboard
provides a more efficient way to monitor affordability and prioritize
interventions.\
It enables:

- Rapid identification of high-burden neighborhoods

- Clear comparisons between market conditions across boroughs

- Insight into whether affordable housing supply corresponds to areas
  with the greatest financial strain

- A repeatable, automated workflow that reduces reliance on manual data
  collection

These practical improvements can support planning decisions, resource
allocation, and ongoing program evaluation.

### **6.5.2 Theoretical Implications**

The project also demonstrates the value of harmonizing datasets
published at different geographic resolutions.\
By transforming tract-level variables to ZIP-level indicators through
weighted crosswalks, the system shows how consistent spatial units
enhance interpretability and analytical coherence.\
This approach provides a methodological foundation for future urban
informatics projects that require integrating multi-source data into a
single analytical framework.

## 6.6 Summary

In summary, the project successfully developed an integrated data
pipeline and interactive dashboard that unifies income, rent, rent
burden, and affordable housing data across all ZIP codes in New York
City. By implementing automated ETL processes, standardized database
structures, and geospatial visualization tools, the system offers a
clearer and more accessible framework for analyzing housing
affordability. The resulting unified spatial dataset enables consistent
cross-neighborhood comparisons and reveals distinct affordability
patterns, including pronounced rent burdens in lower-income communities
and substantial geographic variation in both market rents and household
incomes. The analysis also highlights observable mismatches between the
locations with the greatest affordability pressures and the distribution
of affordable housing supply. Furthermore, automation contributed to a
marked reduction in data processing time, improving data freshness and
reliability. Taken together, these outcomes provide a comprehensive and
analytically coherent view of housing affordability conditions in New
York City, strengthening the foundation for both empirical research and
policy-oriented decision-making.

## 6.7 Repository of Data Sets and Code

All datasets and the full codebase for the ETL pipeline, FastAPI
backend, and Streamlit dashboard are available at:
<https://github.com/Becky0713/NOAH>

This repository constitutes the complete technical record of the NYC
Affordable Housing Dashboard and contains all materials necessary to
reproduce the ETL pipeline, backend services, database schema, frontend
interface, and deployment environment.

The repository's root directory includes the core FastAPI backend
implementation and the data-processing scripts responsible for
harmonizing and transforming the various housing datasets used in the
project. These scripts perform tasks such as variable standardization,
type cleaning, ZIP-code crosswalk operations, rent burden calculations,
and the ingestion of processed tables into PostgreSQL/PostGIS. The
backend code also defines the project's REST API endpoints, which
provide structured JSON and GeoJSON outputs to the dashboard interface.

A collection of technical documentation is included in the form of
multiple Markdown files. These documents describe the required
PostgreSQL/PostGIS configuration (DATABASE_SETUP.md), the structure and
loading procedure for the project's database schema
(DATABASE_INTEGRATION_GUIDE.md), and the workflow for connecting DBeaver
and other interfaces to the cloud-hosted database
(DBEAVER_TO_STREAMLIT.md). Additional documents, including the
deployment guides (DEPLOYMENT.md, QUICK_DEPLOY.md, and
FREE_DEPLOYMENT.md), specify the steps needed to deploy the system on
Render, Fly.io, or alternative cloud platforms. These guides are
accompanied by the relevant configuration files, such as Dockerfile,
docker-compose.yml, Procfile, fly.toml, and render.yaml, which together
define the containerized environment used for backend deployment.

The frontend Streamlit dashboard is contained within a dedicated folder
in the repository and includes the full application code used to
generate the project's interactive maps, affordability indicators,
ZIP-level lookups, and filter-based exploration tools. Configuration
files stored in the .streamlit directory specify the runtime environment
and theme settings for the deployed dashboard. The interface draws
directly from the FastAPI backend and the cloud-hosted PostgreSQL
database through secure connections documented in the repository's
integration notes.

Finally, the repository contains a set of auxiliary materials that
supported development, including migration notes, rent burden
documentation, free-database options, and project progress logs.
Together, the codebase and documentation form a fully reproducible
environment that enables future researchers, policy analysts, and
practitioners to extend, audit, or redeploy the dashboard. The
repository therefore serves not only as an archive of the project's
technical work but also as a reference implementation for building
integrated housing data systems leveraging modern spatial database and
cloud technologies.

*\*

# **Issues Encountered**

During the development of the NOAH Affordable Housing Dashboard, several
issues emerged across data acquisition, ETL implementation, database
design, and deployment. While none of these issues threatened the
overall project timeline, each required timely resolution to maintain
data quality, system stability, and analytical consistency. This section
summarizes the main issues encountered and describes how they were
addressed, as well as how they relate to the risk management plan.

## **7.1 Data Quality and Inconsistent Formats**

One of the earliest challenges involved inconsistencies across datasets
obtained from ACS, StreetEasy, PLUTO, and various NYC Open Data portals.
The formatting of ZIP codes, tract identifiers, and GEOIDs varied widely
across files. Some datasets used strings, others used integers; some ZIP
codes dropped leading zeros; and some fields included hyphens or
irregular spacing.

These inconsistencies caused upload failures in PostgreSQL, table schema
mismatches, and difficulty joining tables during ETL. Some datasets
contained non--New York City entries, blank values, or incomplete
fields.

**How the issue was handled:**

- Implemented uniform typing and formatting rules in the ETL scripts
  (e.g., converting ZIP codes to five-digit strings).

- Added steps to remove hyphens, spaces, and invalid identifiers.

- Dropped non-NYC observations and rows with unrecoverable missing
  values.

- Standardized column naming across all datasets before uploading to the
  cloud database.

- Built SQL-level constraints (e.g., primary keys, NOT NULL rules) to
  prevent accidental ingestion of malformed data.

This issue was anticipated in the risk management plan under **"Data
Integrity Risk"**, and the mitigation strategy---consistent data
validation and quality checks---successfully prevented downstream
errors.

## **7.2 Geographic Misalignment Between Tract-Level and ZIP-Level Data**

A major structural challenge was that ACS indicators (rent burden,
income, demographics) are published at the census-tract level, while
StreetEasy rental data exists at the ZIP-code level. Directly merging
these datasets is impossible without geographic harmonization.

Initially, attempts to merge ACS tracts with ZIP data resulted in
duplicate rows, incorrect aggregations, or mismatched geometry coverage.

**How the issue was handled:**

- Integrated an external tract-to-ZIP crosswalk with population-based
  allocation factors.

- Added weighted calculations to allocate tract values proportionally to
  ZIPs.

- Validated ZIP-level results by comparing row counts and geographic
  coverage with USPS ZIP boundaries.

This issue was included in the risk plan as **"Geographic Resolution
Mismatch"**, and the planned mitigation---using a validated
crosswalk---resolved the misalignment effectively.

## **7.3 SQL Table Creation Errors and Cloud Database Upload Failures**

Throughout development, multiple issues occurred during PostgreSQL table
creation and cloud database uploads:

- Columns with the same name but different data types

- Attempts to add columns that already existed

- Geometry fields failing to upload due to invalid shapes

- Insertions failing because of batch-insert errors in DBeaver

These issues blocked ETL progress and temporarily prevented the
dashboard from showing updated values.

**How the issue was handled:**

- Dropped and recreated problematic tables using clean schemas.

- Introduced explicit data-type casting in Python (e.g., ensuring
  numeric fields were uploaded as floats instead of text).

- Added PostGIS functions (ST_MakeValid) to fix invalid geometries.

- Disabled batch insert in DBeaver when necessary.

- Established a naming convention for all database tables to keep the
  schema clean and predictable.

This was partially predicted in the risk plan as **"Database Schema
Risk"**, and the contingency---allowing for iterative rebuilds and
backup scripts---was used to resolve the issues.

## **7.4 Spatial Rendering Issues in PyDeck**

During visualization, ZIP-code shapes sometimes failed to render or
appeared distorted due to invalid polygons or missing geometry rows in
the database. Additionally, non-NYC ZIPs were initially included, making
the map cluttered and misleading.

**How the issue was handled:**

- Filtered geometry tables to include only NYC ZIP codes.

- Repaired geometry using PostGIS and validated polygon integrity.

- Re-exported the corrected geojson for use in PyDeck.

This issue was not explicitly listed in the original risk plan but
relates to the broader category of **"Visualization Risk"**. The
resolution improved map clarity and ensured that users see only
NYC-relevant shapes.

## **7.5 API Connectivity and Deployment Limitations**

When deploying the backend on Render, intermittent API timeouts and
schema mismatches occurred. The frontend occasionally attempted to
access endpoints before the backend finished initializing, resulting in
404 errors or incomplete data loads.

**How the issue was handled:**

- Added health-check routes and delayed frontend map loading until API
  responses were confirmed.

- Updated API documentation and tightened Pydantic schema validation.

- Applied retry logic for selected queries to improve stability.

This issue aligns with the risk plan category **"Deployment and Hosting
Risk"**, and the mitigation strategies---API validation and retry
logic---helped maintain uptime.

## **7.6 Project Scope Adjustment**

Initially, the dashboard included a planned "Access & Complaint Data"
module (311 complaints, CouncilStat). However, due to time constraints
and inconsistent formatting of these datasets, the module was removed
from the final scope.

**How the issue was handled:**

- The scope was narrowed to the four highest-value modules: income,
  rent, rent burden, and affordable housing supply.

- The database structure was simplified accordingly, reducing complexity
  and ensuring a complete, high-quality final deliverable.

This falls under **"Scope Risk"** in the risk plan, and adjusting the
scope early prevented delays.

## 7.7 Risk management plan

At the outset of the project, several categories of risks were
anticipated, including potential changes to public APIs, inconsistencies
across NYC open datasets, spatial resolution mismatches, cloud
deployment failures, and time limitations. To address these risks,
contingency strategies were prepared in advance, such as maintaining
backup data exports, implementing schema validation prior to database
upload, establishing a staging environment for deployment testing, and
prioritizing core features when time constraints became binding.

During implementation, the most significant issue encountered was data
inconsistency across multiple public sources. These discrepancies
included missing values, invalid GEOIDs, and ZIP-code formats that
conflicted across datasets. This issue had been anticipated, and the
planned mitigation---schema standardization and field-level
validation---was applied immediately, ensuring reliable ingestion and
preventing downstream errors in the database and dashboard.

A second issue arose from the geographic mismatch between tract-level
ACS variables and ZIP-level market rent data. The predefined contingency
strategy---using a population-weighted tract-to-ZIP crosswalk---was
implemented to harmonize the datasets. This allowed indicators from
different spatial units to be aggregated consistently and enabled
ZIP-level visualizations.

Deployment also presented challenges, including table-creation
conflicts, geometry-field errors, and temporary failures in cloud
hosting. These problems were resolved by reverting to a staging
environment, rebuilding tables with clean schemas, and enforcing strict
data-type consistency. This approach minimized downtime and protected
the integrity of the development workflow.

Finally, the limited project timeline required deprioritizing
non-essential modules, such as the Access & Complaint data component.
Following the predefined time-management contingency, core
analytics---rent burden, market rent, income, and spatial
visualization---were completed first, ensuring the delivery of a fully
functioning dashboard within the available hours.

Overall, the issues encountered aligned with the risks anticipated at
project initiation, and the prepared mitigation strategies proved
effective. These measures ensured stable progress, maintained data
integrity, and enabled successful completion of the NOAH Affordable
Housing Dashboard.

# Lessons Learned

Throughout the development of the NOAH Affordable Housing Dashboard, I
gained a number of technical, analytical, and project management skills
that significantly expanded my capability as both a data analyst and a
systems developer. Although the project was successfully completed on
time and achieved the expected level of quality, the learning experience
proved even more valuable than the deliverable itself.

One of the most important lessons I gained was a deeper understanding of
**end-to-end data engineering workflows**. Prior to this project, I had
experience with data cleaning and analysis, but building an integrated
pipeline---from raw public data APIs, to ETL processing in Python, to a
structured PostgreSQL/PostGIS cloud database---required me to approach
data from a more architectural perspective. I learned how to design
database schemas, handle geo-spatial data, normalize inconsistent
formats, manage crosswalk transformations, and maintain data quality
across multiple sources. These are skills I had never applied at this
scale before, and they fundamentally changed how I think about the
reliability and reproducibility of analysis.

Another major area of growth was **full-stack system development**. I
learned how to deploy a FastAPI backend, connect it to a cloud database,
and design a Streamlit dashboard that could dynamically load geospatial
layers. Prior to this project, I had never built a web-based tool that
combined live API endpoints with interactive map visualizations.
Debugging deployment issues, handling asynchronous data loads, and
optimizing database performance taught me how different system
components interact---and how easily one misalignment can break the
entire workflow.

In addition, this project strengthened my **project and risk management
abilities**. Throughout the 100-hour development timeline, I had to
prioritize core functions, manage scope, and adjust expectations based
on technical constraints. Several risks identified early---such as API
instability, schema inconsistencies, and limited development time---did
materialize during the project. Successfully resolving them using the
planned contingency strategies showed me how valuable risk planning is,
especially when working on a complex technical system with many
dependencies.

Finally, I learned the importance of **clear communication and
stakeholder alignment**. Regular updates with my sponsor helped ensure
that the project's direction remained aligned with real research needs
at the Urban Lab. Their feedback also helped me refine features such as
map clarity, dataset filtering, and the usability of the dashboard
interface. This experience taught me how iterative feedback, version
tracking, and expectation management contribute directly to project
quality.

Overall, the project was an invaluable learning experience. It allowed
me to bridge data engineering, geospatial analytics, backend
development, and visualization into a single integrated system. More
importantly, it strengthened my ability to plan, execute, and deliver a
complex technical project from scratch---skills that I will carry
forward into future professional and academic work.

# **Conclusion and Further Work**

## **9.1 Conclusions**

### **9.1.1 Overall Outcomes**

The primary goal of this project was to create an integrated, automated,
and user-friendly data platform that consolidates NYC affordable housing
datasets into a single dashboard for spatial analysis and
decision-making. This goal was fully achieved. The resulting system
successfully aggregates data across income, rent, rent burden, and
affordable housing supply, and presents them through interactive
geospatial visualizations supported by a robust backend and spatial
database.

### **9.1.2 Key Findings**

The analysis revealed several notable patterns regarding housing
affordability across New York City. First, rent burden levels remain
persistently high across nearly all ZIP codes, suggesting that
affordability pressures are not confined to specific neighborhoods but
instead represent a citywide structural challenge. Spatial patterns in
rental prices further show that Manhattan and parts of Northwest
Brooklyn exhibit the highest median rents, whereas much of Queens and
the Bronx continue to provide relatively lower-cost housing options.

The data also indicate that rent burden tends to be most pronounced in
lower-income neighborhoods; however, unexpectedly high burden levels
appear in several affluent ZIP codes as well. These cases likely reflect
the combined effects of extremely elevated market rents and behavioral
factors among higher-income renters, including preferences for location
or amenities that lead to a disproportionate share of income being
allocated toward rent. Additionally, the availability of
income-restricted housing is unevenly distributed. Affordable housing is
comparatively scarce in Midtown Manhattan but more concentrated in Upper
Manhattan, Central Brooklyn, and the Bronx, reinforcing long-standing
disparities in access to subsidized units.

### **9.1.3 Viability Assessment**

The results demonstrate that the proof of concept is both viable and
operationally robust. The automated ETL pipeline successfully reduced
data processing time by more than eighty percent, substantially
improving the frequency and reliability of dataset updates. All
indicators were harmonized at the ZIP-code level, enabling consistent
cross-dataset comparison and eliminating the geographic misalignment
that previously complicated analysis.

The dashboard performed reliably during testing, producing stable
geospatial visualizations and supporting interactive exploration of all
key housing indicators without errors or performance issues.
Furthermore, the integration of multiple public datasets into a unified
backend and standardized database schema confirmed the feasibility of
maintaining a consolidated, scalable data infrastructure. Collectively,
these outcomes provide strong evidence that the system is capable of
long-term adoption by research teams, policy analysts, and other
stakeholders engaged in housing affordability studies.

## **9.2 Implications**

### 9.2.1 Theoretical Implications

The project illustrates the value of geographic harmonization when
integrating multi-source urban data. It shows that tract-level ACS
variables and ZIP-level market rent information can be aligned without
loss of interpretability, enabling clearer cross-neighborhood
comparisons. The methodology contributes to urban informatics by
demonstrating how standardized spatial units improve analytical
robustness and replicate ability.

### 9.2.2 Practical Implications

For policymakers, community organizations, and researchers, the
dashboard enhances the capacity to evaluate housing affordability across
New York City. By enabling rapid identification of neighborhoods with
heightened rent burden and by clarifying spatial disparities in both
rents and household incomes, the tool provides a more systematic
foundation for evidence-based decision-making. The automated data
pipeline substantially reduces the need for manual cleaning and
reconciliation of public datasets, thereby lowering analytical friction
and ensuring that updated information is continuously available.
Moreover, the interface improves transparency and accessibility for
non-technical stakeholders, making complex housing data more
interpretable and actionable. As a result, the dashboard supports more
timely policy responses, facilitates community-level planning, and
strengthens the overall efficiency of affordability analysis within the
urban research ecosystem.

## **9.3 Limitations**

### **9.3.1 Constraints**

### The project operated under several practical and data-related constraints that shaped the scope of the final dashboard. At this stage, the system incorporates only four primary indicators---median rent, household income, rent burden, and affordable housing supply---while additional modules originally planned, such as analysis of 311 housing complaints, were not implemented due to time limitations and data-preprocessing complexity. Moreover, the availability and update frequency of data varied across sources. StreetEasy rental listings are refreshed monthly, whereas American Community Survey indicators are released on an annual cycle, resulting in temporal misalignment among datasets. An additional constraint concerns the nature of rental price information: StreetEasy captures asking rents rather than finalized contract rents, which may introduce upward bias in estimated market conditions depending on neighborhood dynamics and platform usage patterns. These constraints collectively limit the completeness and temporal precision of the current proof of concept.

### 9.3.2 Validity and Bias

Several factors may influence the validity of the dashboard's derived
indicators. Because the American Community Survey provides rent-burden
and income estimates at the census-tract level, the tract-to-ZIP
conversion process relies on survey data that inherently carries
sampling variability. As a result, ZIP-level indicators derived from
these estimates may reflect aggregation noise rather than true
underlying conditions. Additionally, elevated rent-burden rates observed
in higher-income ZIP codes may reflect behavioral or self-selection
dynamics---such as preferences for premium amenities or central
locations---rather than genuine financial strain. Finally, the market
rent estimates depend solely on StreetEasy listings, which tend to be
more prevalent in certain neighborhoods than others, potentially
underrepresenting lower-visibility or low-turnover rental submarkets.
Taken together, these sources of bias underscore the importance of
interpreting dashboard results within their methodological context
rather than viewing them as definitive stand-alone measurements.

### 9.3.3 Limitations of Generative AI for Business Process Re-engineering

Although the development of this project did not rely on generative AI
systems, the broader course objectives necessitate an assessment of
their applicability to business process re-engineering. Generative AI
models face notable limitations in contexts that require high levels of
data fidelity, reproducibility, and auditability. Their outputs can
exhibit inconsistency or factual fabrication, making them unsuitable for
core tasks such as ETL processing, schema harmonization, or spatial data
transformation, where deterministic behavior is essential. Furthermore,
generative transformations often fail to generalize reliably across
datasets with differing structures or metadata conventions, posing risks
in urban informatics workflows that depend on strict standardization and
repeatable execution. These systems also lack transparent decision
pathways, complicating regulatory compliance and public-sector
requirements for traceability. Together, these limitations suggest that
generative AI may serve as a complementary tool for documentation or
exploratory analysis but cannot replace structured, rule-based data
engineering practices in critical housing analytics.

## 9.4 Further Work

### 9.4.1 Next Steps

Several short-term enhancements could meaningfully extend the analytical
capabilities of the system. Incorporating temporal dynamics for rent,
income, and rent burden would allow the dashboard to present changes
over time and better contextualize emerging affordability trends. The
addition of the 311 housing complaints module, contingent on further
data cleaning and normalization, would broaden the dashboard's coverage
of housing-related challenges. Analytical comparisons could also be
strengthened by enabling users to view indicators at alternative
geographic scales, such as boroughs or community districts, thereby
facilitating policy-relevant regional assessments. Moreover, refining
map interactivity---through enhanced tooltips, more precise filtering
logic, and improved responsiveness---would further elevate the usability
of the interface and support more nuanced exploration of affordability
patterns.

### 9.4.2 Long-term Directions

In the longer term, several directions hold promise for transforming the
dashboard into an advanced monitoring and analytical platform.
Predictive modeling could be incorporated to estimate future
affordability risks or to identify neighborhoods likely to experience
rising burdens. Additional indicators such as transportation
accessibility, employment proximity, and measures of demographic
displacement would enrich the analytical framework and offer a more
holistic view of urban housing dynamics. The platform could also be
expanded to support other metropolitan areas or statewide analyses,
providing a standardized infrastructure for cross-city comparisons.
Finally, automated alert mechanisms could be developed to notify
stakeholders when key indicators exceed predetermined thresholds,
enabling earlier intervention and more proactive policy responses.
Together, these developments would shift the system from a descriptive
visualization tool to a dynamic, forward-looking decision-support
system.

## 9.5 Closing Summary

This project contributes an integrated, automated data platform for
analyzing naturally occurring affordable housing in New York City. It
demonstrates how fragmented datasets can be harmonized into a unified
spatial system and visualized through an intuitive dashboard that
improves accessibility and transparency. The final product delivers
meaningful insights into housing affordability patterns and provides a
foundation for continued development in data-driven urban policy
research.

**Repository and Tool Access**

- **Dashboard App:**\
  <https://becky0713-noah-frontendapp-gehyze.streamlit.app/>

- **GitHub Repository (ETL, API, Dashboard Code):**\
  <https://github.com/Becky0713/NOAH>

- All datasets created for the dashboard and the supporting codebase are
  available in the repository, along with the full version of this
  report.

# References

Ambrose, B. W., Coulson, N. E., & Yoshida, J. (2015). The repeat rent
index. *Review of Economics and Statistics, 97*(5), 939--950.

Boeing, G., & Waddell, P. (2017). New insights into rental housing
markets across the United States: Web scraping and analyzing Craigslist
rental listings. *Journal of Planning Education and Research, 37*(4),
457--476.

Colburn, G., & Allen, R. (2018). Rent burden and the Great Recession in
the USA. *Urban Studies, 55*(10), 2265--2285.

Desmond, M., & Wilmers, N. (2019). Do the poor pay more for housing?
*American Journal of Sociology, 125*(3), 1093--1150.

Fields, D., & Uffer, S. (2014). The financialisation of rental housing:
A comparative analysis of New York City and Berlin. *Urban Studies,
53*(7), 1486--1502.

Hankinson, M. (2018). When do renters behave like homeowners? High rent,
price anxiety, and NIMBYism. *American Political Science Review,
112*(3), 473--493.

Meltzer, R., & Schwartz, A. (2016). Housing affordability and health:
Evidence from New York City. *Housing Policy Debate, 26*(1), 80--104.

Seymour, E., Endsley, K., & Franklin, R. S. (2020). Differential drivers
of rent burden in growing and shrinking cities, 1980--2017. *Applied
Geography, 122*, 102240.

Sieg, H., & Yoon, C. (2019). Waiting for affordable housing in New York
City. *Quantitative Economics, 11*(1), 183--217.

Schwartz, A. F. (2019). New York City's Affordable Housing Plans and the
Limits of Local Initiative. *Cityscape, 21*(3), 355--388.\*

Zapatka, S., de Castro, A. M., & Galvão, J. C. (2023). Affordable
regulation? New York City rent stabilization as housing affordability
policy. *City & Community, 22*(4), 884--908.

National Bureau of Economic Research. (2019). *Affordable housing and
city welfare* (Working Paper No. 25906).

NYC Department of Housing Preservation and Development. (2025). *Area
Median Income (AMI) levels and rent limits*. New York, NY.

NYC Rent Guidelines Board. (2025). *Income and Affordability Study*. New
York, NY.

NYC Office of the Comptroller. (2024). *Spotlight: New York City's
rental housing market*. New York, NY.

NYU Furman Center. (Various years). *State of the City: Housing in New
York City* (Citywide data tables). New York, NY.

# Appendix A - Project Acceptance Document

![A project acceptance document with text AI-generated content may be
incorrect.](media/image16.jpg){width="4.604167760279965in"
height="5.958333333333333in"}![A close-up of a certificate AI-generated
content may be
incorrect.](media/image17.png){width="4.935638670166229in"
height="2.513367235345582in"}

# Appendix B - Project Sponsor Agreement

![A list of project management AI-generated content may be
incorrect.](media/image18.png){width="6.5in" height="8.35in"}

![A screenshot of a project information AI-generated content may be
incorrect.](media/image19.png){width="6.3936165791776025in"
height="8.283333333333333in"}

![](media/image20.png){width="6.5in" height="8.365972222222222in"}

![A paper with text on it AI-generated content may be
incorrect.](media/image21.png){width="6.5in"
height="8.410416666666666in"}

![A document with text and words AI-generated content may be
incorrect.](media/image22.png){width="6.5in"
height="8.434027777777779in"}

![A document with text on it AI-generated content may be
incorrect.](media/image23.png){width="6.5in"
height="8.448611111111111in"}

# Appendix C -- Functional Requirements Specifications

**Project Goal**

The goal of this project is to develop an integrated data visualization
dashboard for the NYU Urban Lab to analyze Naturally Occurring
Affordable Housing (NOAH) in New York City. The dashboard will aggregate
data from multiple public APIs to create an interactive, accessible, and
reusable data resource for researchers, urban planners, and civic
stakeholders.

It aims to visualize affordable housing trends, provide tools for
spatial and temporal filtering, and allow users to export customized
datasets for further analysis. The successful completion of this project
will be demonstrated through a stable dashboard that accurately displays
NOAH data, supports interactive mapping and data export, and meets the
satisfaction and approval of the project supervisors, Thomas and
Cameron, for formal delivery to the Urban Lab.

**Project Objectives**

The project will be developed and refined through four clear and
measurable phases. Each phase has specific objectives, measurable
outcomes, and defined completion dates.

**Phase 1: Minimum Viable Product (MVP) Development**\
The first phase focuses on establishing a functional prototype that
connects the front end, back end, and a single database. The Streamlit
framework will be used to build an interactive dashboard displaying NOAH
data from NYC Open Data. A Flask or FastAPI backend will support data
retrieval and communication between layers.\
The metric for success in this phase is a functioning MVP that stably
displays sample NOAH data with full front-end and back-end integration.
This milestone was completed prior to **October 5, 2025.**

**Phase 2: Data Aggregation and Expansion**\
The second phase will enhance the dashboard by integrating additional
data sources to broaden its analytical scope. At least three NYC public
APIs, such as ZOLA, ACRIS, and the U.S. Census, will be incorporated.
Python with Pandas and GeoPandas will be used for automated cleaning,
standardization, and transformation of data, along with scripts to
automate regular updates.\
The metric for success is the successful visualization of integrated
multi-source data within the dashboard and the establishment of an
automated data refresh process. The expected completion date is
**October 31, 2025.**

**Phase 3: Functional and Interaction Optimization**\
The third phase focuses on improving user experience and interface
functionality. The dashboard will provide multi-criteria filtering,
including borough, street, amenities, and project year. It will also
allow users to export filtered data in CSV format with customizable
columns.\
The metric for success is that users can filter data and export accurate
results efficiently, with a loading time of less than three seconds. The
expected completion date is **November 20, 2025.**

**Phase 4: Documentation and Final Delivery**\
The final phase includes comprehensive testing, documentation, and
formal submission of the completed system to the supervisors. This will
include preparing a detailed user manual and API reference, conducting
system validation, and resolving any issues identified during review.\
The metric for success is final approval from supervisors Thomas and
Cameron upon reviewing the delivered system, which will include the
working dashboard, complete documentation, and supporting materials. The
expected completion period is from November 20 through **early December
2025.**

**Requirements Specifications**

The Urban Lab Affordable Housing Dashboard will include several
functional modules designed to achieve the objectives described above.

1.  **User Interface (UI)**\
    A Streamlit-based interactive dashboard will provide access to key
    functions, including the home page, map visualization, data browser,
    and a data dictionary page. Users will be able to filter data,
    explore visualizations, and view thematic insights.

2.  **Data Aggregation Module**\
    This module will automatically retrieve data from public APIs and
    transform it into standardized formats suitable for analysis. Data
    updates can be performed periodically or on demand.

3.  **Database Module**\
    A PostgreSQL database with the PostGIS extension will manage all
    spatial and tabular datasets. It will store affordable housing
    indicators and metadata in a structure optimized for geospatial
    queries.

4.  **Mapping and Visualization Module**\
    The dashboard will include interactive 2D map visualizations built
    using Leaflet or Mapbox, allowing users to view affordable housing
    distributions, filter by attributes, and inspect details via pop-up
    windows.

5.  **Filtering and Query Module**\
    Users will be able to filter data by location, project
    characteristics, and other relevant criteria. Common filters will
    include borough, street, project year, and building amenities.

6.  **Export Module**\
    Users will have the ability to export selected datasets in CSV
    format. They can choose specific columns to include in the export
    file, such as building ID, rent, and total units.

7.  **API Service Module**\
    The system will provide RESTful API endpoints for external
    researchers to access standardized datasets in JSON format.
    Authentication will be handled through secure token mechanisms.

8.  **Security and Privacy**\
    All data transfers will comply with the NYC Open Data License and
    follow general principles of data privacy and security, including
    encrypted communication and controlled access.

9.  **Optional Module: 3D Urban Visualization**\
    A three-dimensional visualization feature may be developed as an
    optional enhancement to display urban structures and related
    metrics. This module is not part of the current core deliverables
    but can be integrated in future iterations.

**Use Case**

**Scenario 1: Tenant User (Emily)**\
Emily is a tenant searching for affordable housing opportunities in New
York City. After logging into the dashboard, she navigates to the
interactive map view. She enters her preferred location in Manhattan
Midtown by specifying a street and avenue. The system automatically
centers the map on the area and highlights affordable housing options
nearby. Emily applies additional filters such as buildings with in-unit
laundry and properties less than ten years old. The dashboard retrieves
matching records and updates the map to show these locations. It also
displays rental trend charts for the selected area. Emily exports the
results as a CSV file, including the housing ID and selected columns, to
compare listings and track her housing search.

**Scenario 2: Researcher User (Daniel)**\
Daniel is a researcher studying affordable housing policies in New York
City. He uses the dashboard to analyze projects initiated between 2015
and 2025. After selecting the project year range and region of interest,
the map updates to display all relevant housing projects. Each marker on
the map includes information such as project name, number of units, and
developer details. Daniel exports the filtered dataset as a CSV file for
further analysis in statistical software. The system ensures that
exported fields match the applied filters, maintaining consistency
between the visualized and exported data.

**Documentation of LLM Prompts**

Part of this document, including the structure of the requirements
specifications and the organization of the use case section, was
generated with assistance from a large language model (OpenAI GPT-5).
The author described the project logic, provided reference materials,
and requested a reformulated and standardized version suitable for
submission. All AI-assisted content was subsequently reviewed and edited
manually to ensure accuracy and alignment with project intentions.

# Appendix D - Project Plan

**Project Tasks Outline**

This project develops a comprehensive and interactive data dashboard
that aggregates and visualizes affordable housing data in New York City
(NOAH -- Naturally Occurring Affordable Housing). It combines public
data APIs, spatial visualization, and database integration to support
urban researchers, planners, and civic stakeholders. The project runs
from **September 1 -- December 15, 2025**.

## **1. Work Breakdown Structure**

### **Level 1 -- Major Milestones**

  --------------------------------------------------------------------------
      **Milestone**           **Start -- **Deliverable**
                              End        
                              Dates**    
  --- ----------------------- ---------- -----------------------------------
  1   Project Initiation and  Sep 1 --   Project scope statement and
      Planning                Sep 15     timeline approved

  2   Data Acquisition and    Sep 16 --  Database schema
      Backend Setup           Oct 5      (PostgreSQL/PostGIS) and ETL
                                         pipeline ready

  3   Frontend and            Oct 6 --   Functional React dashboard and
      Visualization           Nov 10     interactive map
      Development                        

  4   Testing and Technology  Nov 11 --  ETL trial results and UAT completed
      Trial                   Nov 28     

  5   Deployment and          Nov 29 --  Final dashboard deployed with
      Documentation           Dec 15     report and manual
  --------------------------------------------------------------------------

### **Level 2 -- Tasks under Each Milestone**

#### **1. Project Initiation and Planning (Sep 1 -- Sep 15)**

1.1 Define project scope and deliverables\
1.2 Confirm datasets and APIs from NYC Open Data, Census, and HPD\
1.3 Create initial Gantt schedule and assign resources\
1.4 Milestone: Sponsor approval of project plan (Sep 15)

#### **2. Data Acquisition and Backend Setup (Sep 16 -- Oct 5)**

2.1 Design PostgreSQL/PostGIS database schema\
2.2 Develop Python ETL scripts (Pandas + GeoPandas) for data
aggregation\
2.3 Load and validate sample datasets (HPD Affordable Housing, 311
Complaints, Census)\
2.4 Integrate API connections and data dictionary\
2.5 Milestone: Backend ETL pipeline operational (Oct 5)

#### **3. Frontend and Visualization Development (Oct 6 -- Nov 10)**

3.1 Design UI/UX in Figma based on DePaul and CUSP models\
3.2 Implement React frontend components and navigation\
3.3 Develop Leaflet/Mapbox 2D map and multi-layer visualization\
3.4 Integrate 3D visualizer (Three.js) for building models\
3.5 Link frontend with backend API for real-time queries\
3.6 Milestone: Interactive map and indicator dashboard functional (Nov
10)

#### **4. Testing and Technology Trial (Nov 11 -- Nov 28)**

4.1 Execute automated vs manual ETL trial (Technology Trial Plan)\
4.2 Conduct unit and integration tests for backend API and UI
components\
4.3 Collect performance metrics (update time and error rate)\
4.4 Run User Acceptance Testing (UAT) with Urban Lab team\
4.5 Milestone: Trial results validated and UAT sign-off (Nov 28)

#### **5. Deployment and Documentation (Nov 29 -- Dec 15)**

5.1 Deploy dashboard to cloud (AWS or GCP) using Docker containers\
5.2 Finalize API documentation and user manual\
5.3 Prepare final capstone report and presentation slides\
5.4 Milestone: Project handover and final presentation (Dec 15)

### **Level 3 -- Selected Sub-Tasks (Examples)**

**2.2 Develop ETL scripts:**\
2.2.1 Connect to NYC Open Data APIs\
2.2.2 Implement data cleaning and schema standardization\
2.2.3 Schedule automated loads with cron jobs

**3.3 Leaflet/Mapbox Development:**\
3.3.1 Add layer controls for housing stock and complaints\
3.3.2 Enable geo-filter and time-slider functions\
3.3.3 Test map performance and load times

**4.1 Technology Trial:**\
4.1.1 Run baseline manual data update tests\
4.1.2 Execute automated ETL trial and record metrics\
4.1.3 Analyze results with paired t-test and visuals

## **2. Time Allocation Summary**

  --------------------------------------------------------------------------
  **Phase**                    **Duration**   **Approx. Effort     **Total
                                              (hours / week)**     Hours**
  ---------------------------- -------------- -------------------- ---------
  1\. Project Initiation &     Sep 1 -- Sep   10                   20
  Planning                     15                                  

  2\. Data Acquisition &       Sep 16 -- Oct  15                   45
  Backend Setup                5                                   

  3\. Frontend & Visualization Oct 6 -- Nov   18                   90
  Development                  10                                  

  4\. Testing & Technology     Nov 11 -- Nov  15                   45
  Trial                        28                                  

  5\. Deployment &             Nov 29 -- Dec  12                   36
  Documentation                15                                  

  **Total Estimated Hours**                                        **236
                                                                   hrs**
  --------------------------------------------------------------------------

## **3. LLM Prompt Documentation**

**Prompt Used:**

"Generate a three-level Work Breakdown Structure (WBS) for the *Urban
Lab Affordable Housing Dashboard: A Data Portal for NYC* capstone
project, using the Technology Trial Plan as the mid-term testing phase.
The project runs from September 1 to December 15 2025. Include
milestones, sub-tasks, time allocation, and document the prompt per the
MASY GC-4100 rubric."

**LLM Contribution:**\
The large-language-model (LLM) was used to structure milestones, align
time frames with the Technology Trial Plan, and ensure rubric
compliance. All final task details and sequencing were verified and
refined by the author.

# Appendix E - Risk Management Plan

**Project Overview:**

Urban Lab Affordable Housing Dashboard: A Data Portal for NYC\
This project develops an interactive web-based dashboard integrating NYC
affordable housing data from multiple public APIs. It combines backend
data aggregation, a spatial database, and frontend visualizations to
support urban research and decision-making.

**Total project time budget: 100 hours.**

**Risk Identification**

  ---------------------------------------------------------------------------
   **Number**  **Risk**                            **Probability   **Impact
                                                   Score (1,2 or   Score (1,2
                                                   3)**            or 3)**
  ------------ ----------------------------------- --------------- ----------
       1       Public API structure or endpoints   3               3
               change, breaking automated data                     
               ingestion.                                          

       2       Data inconsistency or missing       2               3
               fields among different NYC datasets                 
               causes integration errors.                          

       3       Backend Flask server or PostgreSQL  2               2
               connection failure interrupts data                  
               access.                                             

       4       Spatial query or PostGIS            2               2
               configuration errors produce                        
               incorrect map results.                              

       5       Cloud hosting or deployment         2               3
               environment misconfiguration causes                 
               downtime.                                           

       6       Frontend React map layers fail to   2               2
               load due to API rate limits or                      
               script errors.                                      

       7       System performance issues (slow     3               2
               response, high memory use) degrade                  
               user experience.                                    

       8       Lack of adequate version control or 2               2
               backup leads to code loss or                        
               rollback delays.                                    

       9       Limited time (100 hours) results in 3               3
               incomplete implementation of                        
               planned features.                                   

       10      Delays in feedback or communication 2               3
               with the supervisor postpone                        
               testing and delivery.                               
  ---------------------------------------------------------------------------

**Risk Matrix**

This matrix places each risk (using the same numbering from the first
table) into the appropriate probability--impact cell.

+-------------+---------------------------------------------------+
|             | RISK (exposure)                                   |
+:===========:+:==========:+:==========:+:==========:+:==========:+
| Probability |            | 1.Slight   | 2\.        | 3\. High   |
| (of         |            |            | Moderate   |            |
| occurrence) |            |            |            |            |
|             +------------+------------+------------+------------+
|             | 1\. Very   |            |            |            |
|             | Unlikely   |            |            |            |
|             +------------+------------+------------+------------+
|             | 2\.        |            | Risk       |  Risk      |
|             | Possible   |            | 3,4,6,8    | 2,5,10     |
|             +------------+------------+------------+------------+
|             | 3\.        |            | Risk 7     |  Risk 1,9  |
|             | Expected   |            |            |            |
+-------------+------------+------------+------------+------------+

**Contingency Plan**

The red-zone risks are: **1, 2, 5, 9, and 10** (all with exposure score
3×3 or 2×3).\
The following contingency strategies were created:

  -------------------------------------------------------------------------------
    No.   Risk Description   Probability   Exposure   Contingency Plan
  ------- ------------------ ------------- ---------- ---------------------------
     1    Public API         3             3          Develop a backup schedule
          structure or                                to regularly export static
          endpoints change,                           CSVs; create a versioned
          breaking automated                          API connector and update
          data ingestion.                             script within 24 hours of
                                                      API change detection.

     2    Data inconsistency 2             3          Build a standardized schema
          or missing fields                           validator to detect missing
          among different                             attributes and
          NYC datasets                                automatically flag
          causes integration                          inconsistent rows for
          errors.                                     manual review before
                                                      database upload.

     5    Cloud hosting or   2             3          Maintain a parallel staging
          deployment                                  server; schedule weekly
          environment                                 deployment tests and
          misconfiguration                            implement automated alerts
          causes downtime.                            for failed builds.

     9    Limited time (100  3             3          Prioritize core
          hours) results in                           functionality (data
          incomplete                                  ingestion, mapping) before
          implementation of                           advanced features; maintain
          planned features.                           a rolling feature backlog
                                                      for post-capstone
                                                      improvements.

    10    Delays in feedback 2             3          Maintain fixed weekly
          or communication                            check-ins; document interim
          with the                                    versions; proceed with
          supervisor                                  internal testing during
          postpone testing                            feedback delays.
          and delivery.                               
  -------------------------------------------------------------------------------

## **Monitoring Plan**

All remaining risks are monitored through weekly progress reviews.\
To minimize probability and limit impact, the project uses:

- Git-based version control

- Frequent database backups

- Structured feature prioritization

- Staged deployment and rollback procedures

- Continuous ETL validation

# Appendix F -- Organizational Change Management Plan

1.  **Objective Clarification**

**Vision:**

The Urban Lab NOAH Dashboard aims to integrate diverse affordable
housing datasets into a unified, interactive internal portal that
enhances research efficiency and data transparency across Urban Lab
projects. The system aligns with Urban Lab's strategic goal of advancing
data-driven urban research and supporting evidence-based policy
analysis.

**Key Outcomes:**

Success will be measured by (1) full deployment of the dashboard with
API-based data integration from at least 10 sources; (2) a \>40%
reduction in manual data collection time for researchers; (3) consistent
data access and visualization for all project members; and (4) a
standardized internal workflow for future data-driven projects.

2.  **Stakeholder Engagement**

**Identify Stakeholders:**

Key stakeholders include Urban Lab researchers, data engineers, project
managers, and affiliated NYU faculty who will directly use and maintain
the dashboard. Indirect stakeholders include student assistants and
partner institutions that contribute datasets or collaborate on
analysis.

**Communication Plan**:

Project communication will be managed through internal meetings and
shared digital workspaces (e.g., Teams, Slack, or Notion). The dashboard
itself will act as the main hub for updates, documentation, and version
tracking, allowing all team members to access current data and project
information as needed.

3.  **Cultural Assessment and Planning Section**

**Current Culture Analysis:**

Urban Lab has a strong culture of research collaboration and innovation
but currently relies on dispersed data management practices and manual
processes. This fragmentation limits efficiency and slows project
turnaround.

**Desired Culture Definition*:***

The dashboard initiative seeks to cultivate a data-driven culture
emphasizing shared standards, collaboration, and automation. It promotes
consistent use of centralized digital tools to strengthen project
transparency and knowledge sharing within the Lab.

4.  **Change Management Section**

**Change Model Adoption:**

The project follows **Kotter's 8-Step Model**, focusing on creating
urgency around the inefficiencies of fragmented data, building a guiding
coalition among research leads, communicating the shared vision for
streamlined workflows, and reinforcing adoption through demonstrated
time savings and improved data accuracy.

**Resistance Management:**

Resistance may arise from staff accustomed to traditional manual data
handling. To address this, early training, open Q&A sessions, and clear
demonstration of the dashboard's efficiency benefits will be
implemented. Feedback will be incorporated iteratively to ensure staff
confidence and ownership of the new system.

5.  **Skills and Capability Enhancement Section**

**Skills Inventory:**

Current team skills include GIS analysis, Python-based data processing,
and housing research expertise. Skill gaps exist in database
administration, API configuration, and version control management.

**Training and Development:**

Training sessions will be conducted internally to enhance familiarity
with PostgreSQL/PostGIS, API documentation practices, and front-end data
visualization. Experienced developers will mentor new members, ensuring
sustainable skill transfer and system maintenance capability.

6.  **Documentation and Communication Section**

**Process Documentation:**

All development stages, from planning to testing, will be logged in a
shared Confluence or GitHub repository. Documentation will include data
dictionaries, schema diagrams, change logs, and troubleshooting records
to ensure reproducibility and transparency across future research
cycles.

**Feedback Mechanisms:**

User feedback will be collected through short internal surveys and
regular debrief meetings. Identified issues or feature requests will be
prioritized in agile sprints, ensuring continuous improvement based on
researcher experience.

7.  **Integration and Adaptation Section**

**Scalability Plan:**

Once fully adopted within Urban Lab, the dashboard will be extended to
support additional research projects and potential collaboration with
other NYU labs. The backend structure (PostGIS and Flask API) allows
seamless integration of new datasets or modules with minimal
reconfiguration.

**Continuous Improvement:**

The project team will maintain quarterly review cycles to evaluate data
freshness, usability, and performance metrics. Feedback-driven
iterations will ensure the platform evolves with research needs and
technological advances.

**PROMPTS**

**Tool Used:** ChatGPT (GPT-5, OpenAI).

**Process and Prompts:**

1.  Uploaded the following reference documents:\
    -- *Urban Lab Affordable Housing Dashboard: A Data Portal for NYC*
    (Project Proposal)\
    -- *Briefing on Creating an Organizational Change Plan* (Fortino,
    2024)\
    -- *The Organizational Change Plan FA24* (Reference Guide)\
    -- *MSMA GC-4115 Organizational Change Plan Briefing Template FA25*
    (Submission Template)

2.  Prompt to AI: "Generate an internal Organizational Change Management
    Plan for the Urban Lab Affordable Housing Dashboard, using the FA25
    template and rubric, with Kotter's 8-Step Model and focus on
    internal adoption within Urban Lab."

3.  Reviewed and revised to align tone and scope with internal
    implementation context.

# Appendix G -- Technology Trial Plan

**Business Task and Objectives**

> Improve the efficiency and reliability of data aggregation and
> visualization for NYC affordable-housing datasets by automating data
> collection and enabling dynamic map-based exploration.

**The Hypothesis**

- Population: Urban Lab researchers and dashboard users.

- Intervention: Automated ETL pipeline (Python + PostgreSQL/PostGIS)
  replacing manual CSV uploads.

- Control: Manual data updates and static Excel-based visualization.

- Expected Outcome: Faster data updates and higher accuracy in dataset
  integration.

Hypothesis Statement:

By introducing an automated data-pipeline using Python and
PostgreSQL/PostGIS, the data-update time will decrease by at least 50%
(from baseline mean T₀ to ≤ 0.5T₀) and data integration accuracy will
improve by 20% compared with manual processing over a two-week trial
period.

**Baseline Metrics and Control Group**

Measure current manual workflow:

- Average update time per dataset (hours).

- Error rate from manual joins (%).\
  Keep the manual process unchanged as the control group for comparison
  with the automated pipeline.\
  Metrics such as processing time and error rate will be recorded
  **daily** during both the baseline and intervention phases to ensure
  consistency.

**The Trial**

• **Duration:** Two weeks (Nov 13 -- Nov 28).

• **Metrics:** Processing time and error rate between manual vs
automated methods.

• **Comparison Plan:** Run both methods on identical datasets and
compare mean differences using a paired t-test and exploratory data
analysis.

Results will be summarized in visual comparison charts and summary
tables to clearly show performance differences.

**The Technology**

> Python ETL script (Pandas + GeoPandas) connected to PostgreSQL/PostGIS
> to automate data download, cleaning, and insertion from NYC Open Data
> APIs.

**Data Collection**

> Record time logs and error counts for each dataset load. Store results
> in a CSV table with the following structure:

- dataset_id (string)

- method (categorical: manual / automated)

- load_time (float, minutes)

- error_rate (float, %)

- timestamp (datetime)

**Data dictionary:** Describes each field's data type, range, and
meaning to ensure data consistency.

**Analysis of Results**

> Compare averages for load_time and error_rate between control and
> intervention groups. Conduct descriptive EDA and paired t-test.
> Visualize results with bar charts.

**Findings and Recommendations**

> If automated pipeline shows significant improvement, recommend full
> integration into dashboard architecture and documentation for Urban
> Lab team. Otherwise, adjust scripts for data validation before
> retesting.

**Documentation of LLM use**

> Prompts used: 'Generate a Technology Trial Plan for Urban Lab
> Affordable Housing Dashboard using automated ETL pipeline as
> intervention.'

# Appendix H - Status Reports

![A project status report with green and yellow dots AI-generated
content may be incorrect.](media/image24.png){width="6.5in"
height="6.980555555555555in"}

![A document with text on it AI-generated content may be
incorrect.](media/image25.png){width="6.5in"
height="7.001388888888889in"}

![A project status report with green and red dots AI-generated content
may be incorrect.](media/image26.png){width="6.5in"
height="6.9631944444444445in"}

![A document with yellow text AI-generated content may be
incorrect.](media/image27.png){width="6.5in" height="7.58125in"}

![A project report with green and yellow dots AI-generated content may
be incorrect.](media/image28.png){width="6.5in" height="8.4125in"}

![A document with text on it AI-generated content may be
incorrect.](media/image29.png){width="6.5in"
height="8.434722222222222in"}

![A document with text on it AI-generated content may be
incorrect.](media/image30.png){width="6.5in" height="8.45625in"}

![A document with text and a note AI-generated content may be
incorrect.](media/image31.png){width="6.5in"
height="7.7972222222222225in"}

![A close-up of a project sponsor AI-generated content may be
incorrect.](media/image32.png){width="6.5in"
height="0.857597331583552in"}

# Appendix I - Annotated Bibliography

1.  Ambrose, B. W., Coulson, N. E., & Yoshida, J. (2015). The repeat
    rent index. Review of Economics and Statistics, 97(5), 939--950.\
    **Ranking:** A\
    **Abstract:** We employ a weighted repeat rent estimator to
    construct quarterly indexes that expand the profession\'s ability to
    make cross-sectional comparisons of housing markets. Our analysis
    shows that there is considerable heterogeneity in the behavior of
    rents across cities over the 2000-2010 decade, but the number of
    cities and years for which nominal rents fell is substantial; rents
    fell in many cities following the onset of the housing crisis in
    2007; and the repeat rent and Bureau of Labor Statistics indexes
    differ due to sampling and construction methods.\
    **ChatGPT provided summary:** This article develops a repeat rent
    index that tracks the same unit across time to control for quality
    and composition. The approach offers a credible way to measure
    rental price change and to compare with hedonic methods.\
    **Researcher comments:** I will cite this as the measurement
    foundation for Market Rent notes. It supports explaining why simple
    medians need caveats about composition and quality.

2.  Boeing, G., & Waddell, P. (2017). New insights into rental housing
    markets across the United States: Web scraping and analyzing
    Craigslist rental listings. Journal of Planning Education and
    Research, 37(4), 457--476.\
    **Ranking:** A\
    **Abstract:** Current sources of data on rental housing---such as
    the census or commercial databases that focus on large apartment
    complexes---do not reflect recent market activity or the full scope
    of the US rental market. To address this gap, we collected, cleaned,
    analyzed, mapped, and visualized eleven million Craigslist rental
    housing listings. The data reveal fine-grained spatial and temporal
    patterns within and across metropolitan housing markets in the
    United States. We find that some metropolitan areas have only
    single-digit percentages of listings below fair market rent.
    Nontraditional sources of volunteered geographic information offer
    planners real-time, local-scale estimates of rent and housing
    characteristics currently lacking in alternative sources, such as
    census data.\
    **ChatGPT provided summary:** The authors present a complete
    workflow for collecting and cleaning listing data, including
    deduplication, geocoding, and screening of outliers. They discuss
    biases and ethics and show how asking rent can be used as a timely
    market signal.\
    **Researcher comments:** I will use this as the main reference for
    constructing and labeling asking-rent indicators and for the caveats
    in the map legend.

3.  Colburn, G., & Allen, R. (2018). Rent burden and the Great Recession
    in the USA. Urban Studies, 55(10), 2265--2285.\
    **Ranking:** A\
    **Abstract:** In the aftermath of the recent recession, the
    percentage of households facing rent burden in the USA reached
    historically high levels, while cost burden for owners has shrunk.
    This study uses two panels from the Survey of Income and Program
    Participation (SIPP) to compare the prevalence, distribution and
    household responses to the phenomenon of rent burden in the USA in
    the years immediately before and after the Great Recession. Results
    suggest that rent burden has become more prevalent after the
    recession and that income, household composition and location are
    major drivers of this phenomenon, both before and after the
    recession. Results also indicate that exiting rent burden was more
    difficult in the years after the recession and that an increasingly
    common coping mechanism for rent burdened households is to increase
    their household sizes. These results indicate that renters have
    experienced increased financial stress related to their housing.
    This finding is notable given the lack of policy responses that
    address hardship among renter households in contrast to the
    privileged status enjoyed by homeowners in the policy domain.\
    **ChatGPT provided summary:** The study examines cost burden before,
    during, and after the Great Recession. It documents persistent
    increases and heterogeneous impacts across metropolitan areas and
    households.\
    **Researcher comments:** This supports using the 30 percent and 50
    percent thresholds and motivates showing burden distributions at
    tract or community district scale.

4.  Desmond, M., & Wilmers, N. (2019). Do the poor pay more for housing?
    American Journal of Sociology, 125(3), 1093--1150.\
    **Ranking:** B\
    **Abstract:** This article examines tenant exploitation and landlord
    profit margins within residential rental markets. Defining
    exploitation as being overcharged relative to the market value of a
    property, the authors find exploitation of tenants to be highest in
    poor neighborhoods. Landlords in poor neighborhoods also extract
    higher profits from housing units. Property values and tax burdens
    are considerably lower in depressed residential areas, but rents are
    not. Because landlords operating in poor communities face more
    risks, they hedge their position by raising rents on all tenants,
    carrying the weight of social structure into price. Since losses are
    rare, landlords typically realize the surplus risk charge as higher
    profits. Promoting a relational approach to the analysis of
    inequality, this study demonstrates how the market strategies of
    landlords contribute to high rent burdens in low-income
    neighborhoods.\
    **ChatGPT provided summary:** The article analyzes rents relative to
    property values and risk. It argues that disadvantaged renters often
    face higher effective prices due to segmentation and constraints.\
    **Researcher comments:** I will use this to interpret spatial
    disparities in rent burden when market rent levels alone do not
    explain observed burdens.

5.  Fields, D., & Uffer, S. (2014). The financialisation of rental
    housing: A comparative analysis of New York City and Berlin. Urban
    Studies, 53(7), 1486--1502.\
    **Ranking:** B\
    **Abstract:** This paper compares how recent waves of private equity
    real estate investment have reshaped the rental housing markets in
    New York and Berlin. Through secondary analysis of separate primary
    research projects, we explore financialisation\'s impact on tenants,
    neighbourhoods, and urban space. Despite their contrasting market
    contexts and investor strategies, financialisation heightened
    existing inequalities in housing affordability and stability, and
    rearranged spaces of abandonment and gentrification in both cities.
    Conversely cities themselves also shaped the process of
    financialisation, with weakened rental protections providing an
    opening to transform affordable housing into a new global asset
    class. We also show how financialisation\'s adaptability in the face
    of changing market conditions entails ongoing, but shifting
    processes of uneven development. Comparative studies of
    financialisation can help highlight geographically disparate, but
    similar exposures to this global process, thus contributing to a
    critical urban politics of finance that crosses boundaries of space,
    sector and scale.\
    **ChatGPT provided summary:** The study links capital flows and
    ownership changes to tenant outcomes and the composition of rental
    stock. It situates NYC within broader financialization trends.\
    **Researcher comments:** I will cite this for Industry and Housing
    Stock context to explain why NOAH units are vulnerable in
    appreciating areas.

6.  Hankinson, M. (2018). When do renters behave like homeowners? High
    rent, price anxiety, and NIMBYism. American Political Science
    Review, 112(3), 473--493.\
    **Ranking:** B\
    **Abstract:** How does spatial scale affect support for public
    policy? Does supporting housing citywide but "Not In My Back Yard"
    (NIMBY) help explain why housing has become increasingly difficult
    to build in once-affordable cities? I use two original surveys to
    measure how support for new housing varies between the city scale
    and neighborhood scale. Together, an exit poll of 1,660 voters
    during the 2015 San Francisco election and a national survey of over
    3,000 respondents provide the first experimental measurements of
    NIMBYism. While homeowners are sensitive to housing's proximity,
    renters typically do not express NIMBYism. However, in high-rent
    cities, renters demonstrate NIMBYism on par with homeowners, despite
    continuing to support large increases in the housing supply
    citywide. These scale-dependent preferences not only help explain
    the deepening affordability crisis, but show how institutions can
    undersupply even widely supported public goods. When preferences are
    scale dependent, the scale of decision-making matters.\
    **ChatGPT provided summary:** Survey experiments show that exposure
    to high housing costs can shift renter attitudes toward development,
    sometimes resembling homeowner preferences.\
    **Researcher comments:** This helps anticipate community responses
    and supports a neutral and explanatory tone in the dashboard
    narrative.

7.  Meltzer, R., & Schwartz, A. (2016). Housing affordability and
    health: Evidence from New York City. Housing Policy Debate, 26(1),
    80--104.\
    **Ranking:** A\
    **Abstract:** It is generally understood that households make
    tradeoffs between housing costs and other living expenses. In this
    article, we examine the relationship between health-related outcomes
    and housing-induced financial burdens for renters in one of the most
    expensive cities in the world, New York, New York. Drawing from the
    Housing Vacancy Survey for 2011, a representative survey conducted
    by the U.S. Census Bureau of more than 16,000 households in New York
    City, we estimate the effect of housing cost burden on the overall
    health of renters and the extent to which they have postponed
    various types of medical services for financial reasons. Results
    show that higher out-of-pocket rent burdens are associated with
    worse self-reported health conditions and a higher likelihood to
    postpone medical services for financial reasons. This relationship
    is particularly strong for those households with severe rent
    burdens. In addition, housing cost burden is equally or more
    important than other physical housing characteristics in explaining
    the variation in self-reported general health status and health care
    postponement. These findings are robust across specifications with
    different degrees of household, unit/building, and neighborhood
    controls, and among longstanding and newer renters. Our findings
    point to the importance of considering health-related outcomes when
    designing housing policies, and that housing subsidies should target
    both renters\' out-of-pocket costs and place-based repair and
    maintenance.\
    **ChatGPT provided summary:** The paper connects rent burden to
    self-reported health and delayed care in NYC. It underscores the
    broader significance of affordability as a policy signal.\
    **Researcher comments:** I will cite this as an NYC-specific anchor
    for rent-burden indicators, without implementing health modules.

8.  Favilukis, Jack, et al. Affordable Housing and City Welfare.
    National Bureau of Economic Research, 2019.\
    **Ranking:** B\
    **Abstract:** Housing affordability is the main policy challenge for
    many large cities in the world. Zoning changes, rent control,
    housing vouchers, and tax credits are the main levers employed by
    policy makers. But how effective are they at combatting the
    affordability crisis? We build a new framework to evaluate the
    effect of these policies on the well-being of its citizens. It
    endogenizes house prices, rents, construction, labor supply, output,
    income and wealth inequality, as well as the location decisions of
    households. Its main novel features are risk, risk aversion, and
    incomplete risk-sharing. We calibrate the model to the New York MSA,
    incorporating current zoning and affordable housing policies.
    Housing affordability policies carry substantial insurance value but
    cause misallocation in labor and housing markets. Housing
    affordability policies that enhance access to this insurance
    especially for the neediest households create large net welfare
    gains.\
    **ChatGPT provided summary:** The working paper evaluates how
    affordable housing policies affect welfare and population
    distribution in cities. It provides a model-based perspective on
    policy mechanisms.\
    **Researcher comments:** I will use this for Housing Stock and
    policy mechanism background. It will not be used as a direct method
    in the UI.

9.  NYC Department of Housing Preservation and Development. (2025). Area
    Median Income (AMI) levels and rent limits. New York, NY.\
    Ranking: A\
    **Abstract:** Official HPD guidance document that lists income
    limits and maximum rents by household size for affordable housing
    programs in New York City.\
    **ChatGPT provided summary:** The HPD AMI table is the authoritative
    source defining how income bands are set in NYC. It translates
    federal HUD AMI levels into city-specific rent limits and
    eligibility thresholds.\
    **Researcher comments:** I will use this to label income categories
    and rent limits in the dashboard; ensures our indicators align with
    official program definitions.

10. NYC Office of the Comptroller. (2024). Spotlight: New York City's
    rental housing market. New York, NY.\
    **Ranking:** B\
    **Abstract:** Official analytical report issued by the NYC Office of
    the Comptroller that reviews recent rental housing trends,
    affordability metrics, and production data across boroughs.\
    **ChatGPT provided summary:** The report compiles recent trends for
    rents, vacancy, production, and burden at city and sub-borough
    levels.\
    **Researcher comments:** I will use this to benchmark levels and
    trend directions for the dashboard indicators.

11. NYC Rent Guidelines Board. (2025). Income and Affordability Study.
    New York, NY.\
    **Ranking:** A\
    **Abstract:** This study highlights year-to-year changes in many of
    the major economic factors affecting NYC's tenant population and
    takes into consideration a broad range of market forces and public
    policies affecting housing affordability, such as unemployment
    rates; wages; housing court and eviction data; and rent and poverty
    levels.\
    **ChatGPT provided summary:** The annual study provides
    authoritative statistics on incomes, rents, and hardship in NYC. It
    includes methodological appendices and consistent definitions.\
    **Researcher comments:** I will cite this repeatedly for current
    figures and definitions for rent burden and income bands.

12. NYU Furman Center. (Various years). State of the City: Housing in
    New York City (Citywide data tables). New York, NY.\
    **Ranking:** B\
    **Abstract:** The State of the City: Housing in New York City
    series, published annually by the NYU Furman Center, provides a
    comprehensive overview of housing, land use, demographics, and
    neighborhood conditions across the five boroughs. Each edition
    compiles citywide and sub-borough data on affordability, rental
    trends, homeownership, and new development, offering consistent
    indicators for longitudinal comparison. The report is a key
    reference for policymakers, planners, and researchers seeking to
    understand housing dynamics and socioeconomic disparities in New
    York City.\
    **ChatGPT provided summary:** This series presents citywide and
    neighborhood statistics with consistent methods. It is widely used
    by agencies and researchers.\
    **Researcher comments:** I will use selected tables to validate
    indicator levels and cross-check definitions.

13. Schwartz, A. (2019). New York City's housing affordability policies
    in context. Cityscape, 21(3), 181--198.\
    **Ranking:** A\
    **Abstract:** This article examines the evolution and outcomes of
    New York City's affordable housing initiatives since the 1980s,
    focusing on the constraints of municipal authority, fiscal
    resources, and land supply. Schwartz argues that while New York City
    has demonstrated exceptional local commitment and policy innovation,
    structural and market limitations prevent city policies from fully
    resolving affordability challenges. The analysis situates local
    actions within the broader context of federal disinvestment and
    state-level policy environments.\
    **ChatGPT provided summary:** The review situates NYC's
    affordability strategy within fiscal and structural constraints. It
    clarifies what city tools can and cannot accomplish.\
    **Researcher comments:** I will cite this in the Industry and
    Problem sections to justify the dashboard's measurement-first scope.

14. Seymour, E., Endsley, K., & Franklin, R. S. (2020). Differential
    drivers of rent burden in growing and shrinking cities, 1980--2017.
    Applied Geography, 122, 102240.\
    **Ranking:** A\
    **Abstract:** Housing affordability is an issue of increasing
    importance and interest, particularly in the United States. Much of
    this interest is due to skyrocketing rents in coastal cities with
    tight housing markets. Shrinking cities, in contrast, are often
    characterized as rich in low-cost housing, providing an affordable
    alternative to superstar cities. This paper compares income and rent
    dynamics in cities with growing versus shrinking populations. While
    costs may be lower in shrinking cities, falling incomes have likely
    rendered housing unaffordable for many residents. We employ multiple
    lines of evidence to test for different dynamics between growing and
    shrinking cities. Matching is used to explore changes in income and
    rent between 1980 and 2017 in shrinking and the most similar
    non-shrinking cities. After controlling for baseline conditions,
    shrinking cities exhibit faster falling incomes and growing cities
    exhibit faster rising rents, while rent burden increases at a very
    similar rate in both groups. We also use a fixed effects regression
    model to test for differences between growing and shrinking cities
    in sensitivity of rent burden to changes in income and rent. Rent
    burden has considerably increased across US cities since 1980, yet
    growing and shrinking cities exhibit clearly different pathways
    toward that end. Shrinking cities are more sensitive to identical
    changes in income and rent, likely because a greater share of their
    residents live near the edge of affordability. •Housing
    affordability is a problem of global dimensions, impacting cities
    throughout the developed world.•Rent burden has increased across
    U.S. cities since 1980, yet growing and shrinking cities exhibit
    different rent and income dynamics.•Shrinking cities exhibit faster
    falling incomes while growing cities exhibit faster rising
    rents.•Shrinking cities are also more sensitive to identical changes
    in income and rent, as a greater share of residents likely live near
    the edge of affordability.\
    **ChatGPT provided summary:** The authors separate the roles of rent
    growth and income change in shaping burden across different urban
    trajectories. They provide long-run evidence on determinants of
    burden.\
    **Researcher comments:** I will use this to interpret changes in
    rent-burden charts and to write notes about rent versus income
    contributions.

15. Sieg, H., & Yoon, C. (2019). Waiting for affordable housing in New
    York City. Quantitative Economics, 11(1), 183--217.\
    **Ranking:** A\
    **Abstract:** We develop a new dynamic equilibrium model with
    heterogeneous households that captures the most important frictions
    that arise in housing rental markets and explains the political
    popularity of affordable housing policies. We estimate the model
    using data collected by the New York Housing Vacancy Survey in 2011.
    We find that there are significant adjustment costs in all markets
    as well as serious search frictions in the market for affordable
    housing. Moreover, there are large queuing frictions in the market
    for public housing. Having access to rent-stabilized housing
    increases household welfare by up to \$65,000. Increasing the supply
    of affordable housing by ten percent significantly improves the
    welfare of all renters in the city. Progressive taxation of
    higher-income households that live in public housing can also be
    welfare improving.\
    **ChatGPT provided summary:** This paper models search and waiting
    in NYC affordable housing allocation. It shows why access frictions
    are central to outcomes. in access.\
    **Researcher comments:** I will cite this when introducing access
    indicators and when explaining that we avoid heavy modeling in the
    UI.

16. Zapatka, S., de Castro, A. M., & Galvão, J. C. (2023). Affordable
    regulation? New York City rent stabilization as housing
    affordability policy. City & Community, 22(4), 884--908.\
    **Ranking:** A\
    **Abstract:** The growing housing affordability crisis is at the
    center of conversations about U.S. inequality. This paper
    reconsiders the role of rent stabilization as one important
    affordability tool. We investigate who is most likely to benefit
    from rent stabilization, how much non-stabilized renters would save
    if their units were stabilized, and the extent to which
    stabilization would reduce rent burden among households. Using New
    York City Housing Vacancy Survey data and employing logistic and
    hedonic regression techniques, we show that Hispanic and
    foreign-born householders are more likely to live in rent-stabilized
    units and find evidence of both rent savings and rent burden
    reduction when comparing stabilized tenants with their
    non-stabilized counterparts. We argue that expanded rent
    stabilization could be paired with policies that stimulate new
    construction to simultaneously curb rent inflation, protect current
    populations from displacement, and increase housing supply.\
    **ChatGPT provided summary:** The study evaluates how rent
    stabilization affects affordability outcomes and who benefits. It
    includes discussion of demographic differences in access.\
    **Researcher comments:** I will use this to interpret observed
    burden patterns in neighborhoods with a high share of stabilized
    units.
