# AI Agent Governance & Roles (AGENTS.md)

This repository implements an **AI Agent Governance** system to oversee software quality, security, user experience, and deployment operations for the `odfinder` application.

---

## 🏛️ Governance Structure

The project features four specialized agent roles that operate coordinately (and sometimes adversarially) to audit code and propose continuous improvements:

| Role | Agent | Primary Focus | Status |
| :--- | :--- | :--- | :--- |
| **CTO** | CTO - Strategic Oversight | Technical lifecycle, strategic viability, risk management, and long-term technical debt. | **Fully Addressed** |
| **Architect** | Technical Lead & Architect | Code structure, concurrency model (thread safety), security (STRIDE), and resource management. | **Fully Addressed** |
| **DevOps** | Solutions & Operations Lead | Continuous integration and delivery (CI/CD), script reliability, multi-platform packaging (.deb), and dependencies. | **Fully Addressed** |
| **UX Designer** | Product & Experience Designer | Usability, GTK visual consistency, accessibility (a11y), and technical documentation. | **Fully Addressed** |

---

## 📂 Audit & Control Documents

All review reports, technical defenses, and action roadmaps are stored under the `docs/governance/` directory:

### 1. Critique & Defense Loops (Critiques)

Located in `docs/governance/critiques/`, each agent maintains its own critique and recommendation loop:

* **CTO**: [cto-strategic-oversight.md](docs/governance/critiques/cto-strategic-oversight.md) (GTK 3 lifecycle, Python 3.10+ migration, and test suite setup) — **Status: Resolved & Mitigated**.
* **Architect**: [technical-lead-architect.md](docs/governance/critiques/technical-lead-architect.md) (GTK threading violation, file descriptor leaks due to unclosed ZIP handlers) — **Status: Resolved & Mitigated**.
* **DevOps**: [solutions-operations-lead.md](docs/governance/critiques/solutions-operations-lead.md) (Lack of CI/CD infrastructure, incomplete dependency declarations) — **Status: Resolved & Mitigated**.
* **UX Designer**: [product-experience-designer.md](docs/governance/critiques/product-experience-designer.md) (Deprecated GTK stock buttons, missing screen reader accessibility) — **Status: Resolved & Mitigated**.

### 2. Strategic Mitigation Plan

* **Roadmap**: [mitigation-plan.md](docs/governance/critiques/mitigation-plan.md) establishes high-priority phases to resolve critical risks (concurrency and file handlers) and modernize the project packaging — **Status: Completed**.

### 3. Codebase Audit Report

* **Technical Report**: [codebase_audit_report.md](docs/governance/audits/codebase_audit_report.md) consolidates the detailed technical findings with Mermaid data flow diagrams, thread boundaries, and code snippets for immediate remediation — **Status: All Findings Resolved & Verified**.

---

## ⚙️ How to Run Agent Audits

Code audits and strategic reviews are managed using the assistant's global workflows:

* **Full Technical Audit**:
  `@[/audit_codebase]`
  *(Analyzes the Python and GTK stack for resource leaks, threading violations, and obsolete configurations).*
  
* **Strategic & Risk Audit**:
  `@[/audit_strategic]`
  *(Evaluates project architecture alignment against technology stack lifecycle standards).*
