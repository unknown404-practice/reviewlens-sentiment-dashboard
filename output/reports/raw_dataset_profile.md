# ReviewLens Raw Dataset Profile
**Generated At:** 2026-09-14 11:31:03  
**Data Mode:** `DEMO`  
**Source:** `Demo Dataset`  
**Dataset Disclaimer:** This demonstration dataset contains synthetic review records deterministically generated with a fixed random seed. It does not represent extracted or scraped marketplace data.

---

## 1. High-Level Summary
- **Total Ingested Rows:** 212
- **Total Columns:** 13
- **Unique Products:** 15
- **Unique Categories:** 5

## 2. Data Quality Audit Metrics
| Metric | Value | Description |
| :--- | :--- | :--- |
| **Total Rows** | `212` | Total raw review records ingested |
| **Total Columns** | `13` | Total schema columns |
| **Fully Duplicate Rows** | `2` | Identical rows across all fields |
| **Duplicate Review Texts** | `4` | Rows sharing identical review text |
| **Missing Review Titles** | `3 (1.4%)` | Records missing a review title |
| **Missing Helpful Votes** | `3 (1.4%)` | Records missing helpful vote count |
| **Invalid Ratings Count** | `4` | Ratings outside 1-5 integer scale |
| **Unique Products** | `15` | Distinct product names represented |
| **Unique Categories** | `5` | Distinct product categories |
| **Earliest Review Date** | `2025-01-15` | Minimum review timestamp |
| **Latest Review Date** | `2026-09-04` | Maximum review timestamp |

## 3. Product Categories Covered
- **Home and Kitchen:** 52 reviews (24.5%)
- **Electronics:** 41 reviews (19.3%)
- **Beauty and Personal Care:** 41 reviews (19.3%)
- **Books:** 40 reviews (18.9%)
- **Sports and Outdoors:** 38 reviews (17.9%)

---
*Profile generated automatically by ReviewLens Data Foundation Pipeline.*
