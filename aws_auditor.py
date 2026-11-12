import os
import time
import boto3
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Initialize Gemini client (explicitly using v1beta for Gemini 3 models) and AWS EC2 client
ai_client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options={"api_version": "v1beta"},
)
aws_region = os.environ.get("AWS_REGION", "ap-south-1")
ec2 = boto3.client("ec2", region_name=aws_region)

# --- REAL AWS BOTO3 DIAGNOSTIC TOOLS ---
def audit_open_security_groups() -> str:
    """Scans AWS Security Groups for risky 0.0.0.0/0 public inbound access."""
    print("🛠️ [AWS TOOL] Scanning Security Groups for 0.0.0.0/0 rules...")
    response = ec2.describe_security_groups()
    risky_rules = []

    for sg in response.get("SecurityGroups", []):
        for perm in sg.get("IpPermissions", []):
            for ip_range in perm.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    from_port = perm.get("FromPort", "All")
                    to_port = perm.get("ToPort", "All")
                    risky_rules.append(
                        f"SG: {sg['GroupName']} ({sg['GroupId']}) allows 0.0.0.0/0 on ports {from_port}-{to_port}"
                    )

    return "\n".join(risky_rules) if risky_rules else "No 0.0.0.0/0 inbound rules found."

def audit_unattached_ebs_volumes() -> str:
    """Finds unattached EBS volumes ('available' state) wasting monthly AWS spend."""
    print("🛠️ [AWS TOOL] Scanning for unattached EBS volumes...")
    response = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
    volumes = response.get("Volumes", [])

    if not volumes:
        return "No unattached EBS volumes found. Storage is clean."

    waste_list = [
        f"Volume {v['VolumeId']} | Size: {v['Size']} GiB | Type: {v['VolumeType']} | State: available"
        for v in volumes
    ]
    return "\n".join(waste_list)

def audit_stopped_ec2_instances() -> str:
    """Checks for stopped EC2 instances that may still incur EBS storage charges."""
    print("🛠️ [AWS TOOL] Scanning for stopped EC2 instances...")
    response = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}])
    stopped = []

    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            stopped.append(f"Instance {inst['InstanceId']} ({inst['InstanceType']}) is stopped.")

    return "\n".join(stopped) if stopped else "No stopped EC2 instances found."

# --- AUTONOMOUS AWS AUDITOR LOOP ---
def run_aws_auditor():
    prompt = f"""
    You are a Principal AWS Cloud Security & FinOps Architect auditing AWS region {aws_region}.
    1. Call ALL THREE AWS diagnostic tools (`audit_open_security_groups`, `audit_unattached_ebs_volumes`, `audit_stopped_ec2_instances`) to inspect the live account.
    2. Produce a clean, executive **AWS Security & FinOps Audit Report** containing:
       - Security Findings & Risk Severity (High/Medium/Low)
       - FinOps Cost-Saving Opportunities
       - Exact AWS CLI & Terraform remediation snippets for any findings.
    """

    tools = [audit_open_security_groups, audit_unattached_ebs_volumes, audit_stopped_ec2_instances]
    models_to_try = ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-3.1-pro-preview"]

    for model_name in models_to_try:
        for attempt in range(1, 3):
            try:
                print(f"🤖 Starting AWS AIOps Auditor using {model_name} (Attempt {attempt})...")
                response = ai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(tools=tools, temperature=0.2),
                )
                print("\n" + "="*60)
                print(f"☁️ LIVE AWS SECURITY & FINOPS AUDIT REPORT ({aws_region})")
                print("="*60)
                print(response.text)
                return
            except APIError as e:
                print(f"⚠️ Temporary API issue on {model_name}: {e.message}")
                time.sleep(5)

    raise RuntimeError("All fallback models temporarily unavailable.")

if __name__ == "__main__":
    run_aws_auditor()
