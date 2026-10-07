# Deploying on AWS

Target setup: a single EC2 instance running the whole stack with Docker Compose
(PostgreSQL + FastAPI + Streamlit), with uploaded originals stored in S3.

```
            ┌──────────────── EC2 (Docker Compose) ────────────────┐
 user ──▶ :8501  Streamlit ──HTTP──▶ :8000  FastAPI ──▶ PostgreSQL  │
            │                              │                       │
            └──────────────────────────────┼───────────────────────┘
                                           ▼  (IAM role, no keys)
                                       Amazon S3
```

## 1. S3 bucket

1. Create a bucket (e.g. `arabic-doc-intel-<your-name>`) in your region. Keep
   **Block all public access** on — the API reads files back itself, nothing is public.

## 2. IAM role for the instance

1. IAM → Policies → Create policy → JSON → paste `s3-access-policy.json`
   (replace `YOUR-BUCKET-NAME`).
2. IAM → Roles → Create role → trusted entity **EC2** → attach that policy.

The app uses boto3's default credential chain, so on EC2 it picks up the role
automatically — no access keys in `.env` or in the repo.

## 3. EC2 instance

| Setting | Value |
|---|---|
| AMI | Amazon Linux 2023 |
| Type | `t3.medium` (4 GB RAM) recommended; `t3.small` + swap works but is slow |
| Storage | 20 GB gp3 (the image with PyTorch + AraBERT is several GB) |
| IAM instance profile | the role from step 2 |
| Security group | inbound **8501** (dashboard) from anywhere; **22** (SSH) from your IP only. Keep **8000** closed unless you want the API public. |
| User data | contents of `user-data.sh` |

The first boot builds the image (downloads PyTorch + AraBERT, trains the head), which
takes several minutes. Then open `http://<public-ip>:8501`.

## 4. Switch uploads to S3

SSH in, edit `/opt/arabic-doc-intel/.env`:

```
STORAGE_BACKEND=s3
S3_BUCKET_NAME=arabic-doc-intel-<your-name>
AWS_REGION=<bucket region>
```

then `docker compose up -d`.

## Updating

```bash
cd /opt/arabic-doc-intel && git pull && docker compose up -d --build
```

## Cost control

- **Stop** the instance when you aren't demoing — you pay for compute only while it runs
  (the EBS disk is still billed, a few dollars a month).
- Set an **AWS Budget** alert before launching anything.
- The public IP changes after stop/start unless you attach an Elastic IP (which is billed).

## Possible next steps

- Move PostgreSQL to **Amazon RDS** (just point `DATABASE_URL` at it).
- Put the dashboard behind HTTPS (Nginx + Let's Encrypt, or an Application Load Balancer).
- Describe this setup as code with Terraform.
