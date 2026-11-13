import os
import time
import boto3
from botocore.config import Config
from google import genai
from google.genai import types

print("🚀 Initializing Gemini and AWS clients...", flush=True)

ai_client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(api_version="v1beta", timeout=60_000),
)

aws_region = os.environ.get("AWS_REGION", "ap-south-1")
boto_config = Config(connect_timeout=10, read_timeout=10, retries={"max_attempts": 2})
ec2 = boto3.client("ec2", region_name=aws_region, config=boto_config)

# --- REAL AWS BOTO3 DIAGNOSTIC TOOLS ---
def audit_open_security_groups() -> str:
    """Scans AWS Security Groups for risky 0.0.0.0/0 public inbound access."""
    print("🛠️ [AWS TOOL] Scanning Security Groups for 0.0.0.0/0 rules...", flush=True)
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

    print("✅ [AWS TOOL] Security Groups scan complete.", flush=True)
    return "\n".join(risky_rules) if risky_rules else "No 0.0.0.0/0 inbound rules found."

def audit_unattached_ebs_volumes() -> str:
    """Finds unattached EBS volumes ('available' state) wasting monthly AWS spend."""
    print("🛠️ [AWS TOOL] Scanning for unattached EBS volumes...", flush=True)
    response = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])
    volumes = response.get("Volumes", [])

    print("✅ [AWS TOOL] EBS Volumes scan complete.", flush=True)
    if not volumes:
        return "No unattached EBS volumes found. Storage is clean."

    waste_list = [
        f"Volume {v['VolumeId']} | Size: {v['Size']} GiB | Type: {v['VolumeType']} | State: available"
        for v in volumes
    ]
    return "\n".join(waste_list)

def audit_stopped_ec2_instances() -> str:
    """Checks for stopped EC2 instances that may still incur EBS storage charges."""
    print("🛠️ [AWS TOOL] Scanning for stopped EC2 instances...", flush=True)
    response = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}])
    stopped = []

    for reservation in response.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            stopped.append(f"Instance {inst['InstanceId']} ({inst['InstanceType']}) is stopped.")

    print("✅ [AWS TOOL] EC2 Instances scan complete.", flush=True)
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
  MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]

    for model_name in MODELS:
        for attempt in range(1, 4):
            try:
                print(f"🤖 Starting AWS AIOps Auditor using {model_name} (Attempt {attempt})...", flush=True)
                chat = ai_client.chats.create(
                    model=model_name,
                    config=types.GenerateContentConfig(tools=tools, temperature=0.2),
                )
                response = chat.send_message(prompt)

                print("\n" + "="*60, flush=True)
                print(f"☁️ LIVE AWS SECURITY & FINOPS AUDIT REPORT ({aws_region})", flush=True)
                print("="*60, flush=True)
                print(response.text, flush=True)
                return
            except Exception as e:
                wait_seconds = attempt * 10
                print(f"⚠️ Issue on {model_name} (Attempt {attempt}): {type(e).__name__}: {e}", flush=True)
                print(f"⏳ Waiting {wait_seconds}s before next attempt...", flush=True)
                time.sleep(wait_seconds)

    raise RuntimeError("All fallback models failed or experienced high demand.")

if __name__ == "__main__":
    run_aws_auditor()
