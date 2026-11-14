# 🛡️ AWS AIOps Security & FinOps Auditor

![AWS Audit](https://github.com/anu7053/aws-aiops-security-finops-auditor/actions/workflows/aws-audit.yml/badge.svg)

An autonomous, AI-powered cloud governance agent built with Python and the Google GenAI SDK (`gemini-3.8-flash`). Automated via GitHub Actions, this pipeline securely authenticates into AWS using keyless OpenID Connect (OIDC) to inspect live cloud infrastructure, detect security misconfigurations, and identify FinOps cost-optimization opportunities.

---

## 🏗️ Architecture & Workflow

1. **Keyless AWS Authentication (OIDC):** GitHub Actions assumes an AWS IAM Role dynamically via OpenID Connect—eliminating static, long-lived `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets.
2. **Autonomous Tool-Calling Agent (`aws_auditor.py`):** Uses Gemini function calling (`tools`) at a low temperature (`0.2`) to deterministically query live AWS resources and generate a structured **Live AWS Security & FinOps Audit Report**.
3. **Fault-Tolerant Resilience:** Implements retry backoff and graceful exit handling (`sys.exit(0)`) to cleanly navigate upstream API capacity spikes (`503`) or free-tier daily quota limits (`429`) without breaking CI/CD builds.

---

## 🚀 Key Features

* **Zero-Trust CI/CD Security:** Short-lived, scoped session credentials via AWS IAM OIDC Identity Provider.
* **Combined Security & FinOps Insights:** Audits IAM/network posture alongside idle or underutilized cloud spend in a single automated run.
* **On-Demand & Scheduled Execution:** Triggered manually via `workflow_dispatch` or on a recurring cron schedule.

---

## 🛠️ Tech Stack

* **AI / LLM:** Google GenAI SDK (`gemini-3.8-flash`)
* **Cloud & Security:** AWS IAM (OIDC Federation), Boto3
* **CI/CD Automation:** GitHub Actions (`aws-audit.yml`)
* **Language:** Python 3.11

---

## ⚙️ Setup & Configuration

### 1. AWS IAM OIDC Setup
1. Create an **IAM OIDC Identity Provider** in AWS for `token.actions.githubusercontent.com`.
2. Create an **IAM Role** with a trust policy restricted to your GitHub repository (`anu7053/aws-aiops-security-finops-auditor`).
3. Attach read-only security and billing/cost policies (e.g., `SecurityAudit`, `ViewOnlyAccess`).

### 2. GitHub Repository Secrets
Add the following secrets under **Settings > Secrets and variables > Actions**:

| Secret Name | Description |
| :--- | :--- |
| `AWS_ROLE_ARN` | The ARN of the IAM Role configured for GitHub OIDC |
| `AWS_REGION` | Target AWS region to audit (e.g., `us-east-1`, `ap-south-1`) |
| `GEMINI_API_KEY` | Your Google AI Studio API key |

### 3. Running the Pipeline
* Navigate to the **Actions** tab in GitHub.
* Select **AWS AIOps Security & FinOps Audit**.
* Click **Run workflow** (`workflow_dispatch`) to execute a live audit.

---

## 📂 Repository Structure

```text
├── .github/
│   └── workflows/
│       └── aws-audit.yml      # GitHub Actions CI/CD workflow definition
├── aws_auditor.py             # Core AI agent, AWS tool bindings, and retry logic
├── requirements.txt           # Python dependencies (google-genai, boto3)
└── README.md                  # Project documentation
