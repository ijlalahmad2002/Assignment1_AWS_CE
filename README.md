# Assignment1_AWS_CE
# UniEvent — University Event Management System on AWS

A cloud-hosted web application where students can browse university events, fetched automatically from the Ticketmaster API and deployed on AWS using EC2, S3, ELB, VPC, and IAM.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [AWS Architecture](#aws-architecture)
3. [Technologies Used](#technologies-used)
4. [Project File Structure](#project-file-structure)
5. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
   - [Step 1: Get Ticketmaster API Key](#step-1-get-ticketmaster-api-key)
   - [Step 2: Set Up AWS IAM Role](#step-2-set-up-aws-iam-role)
   - [Step 3: Create VPC and Subnets](#step-3-create-vpc-and-subnets)
   - [Step 4: Create S3 Bucket](#step-4-create-s3-bucket)
   - [Step 5: Launch EC2 Instances](#step-5-launch-ec2-instances)
   - [Step 6: Deploy the Application](#step-6-deploy-the-application)
   - [Step 7: Set Up Elastic Load Balancer](#step-7-set-up-elastic-load-balancer)
   - [Step 8: Test the System](#step-8-test-the-system)
6. [How the Application Works](#how-the-application-works)
7. [Security Design](#security-design)
8. [Fault Tolerance](#fault-tolerance)

---

## Project Overview

UniEvent is a centralized platform where students can:
- Browse university events automatically fetched from the **Ticketmaster Discovery API**
- View event details including title, date, venue, and description
- See event poster images stored securely in **Amazon S3**

The system is designed to be **secure**, **scalable**, and **fault-tolerant** using AWS best practices.

---

## AWS Architecture

```
Internet (Students)
        |
        v
[Elastic Load Balancer]  <-- Public Subnet (AZ-a & AZ-b)
        |
   _____|_____
  |           |
  v           v
[EC2 - AZ-a] [EC2 - AZ-b]  <-- Private Subnet (no direct internet)
  |           |
  v           v
[Amazon S3 Bucket]  <-- Event images stored here
        ^
        |
[Ticketmaster API]  <-- External events fetched every 30 min
        
[IAM Role]  <-- Grants EC2 permission to access S3
[VPC]       <-- Isolates all resources in private network
```

**Key design decisions:**
- EC2 instances live in **private subnets** — students cannot access them directly
- The **Load Balancer** in the public subnet is the only entry point
- Two EC2 instances across **two Availability Zones** — if one fails, traffic routes to the other
- **IAM roles** are used instead of hardcoded credentials — more secure

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 + Flask | Web application framework |
| AWS EC2 | Virtual servers running the app |
| AWS S3 | Storing event poster images |
| AWS ELB | Distributing traffic across EC2 instances |
| AWS VPC | Private network isolation |
| AWS IAM | Secure permissions management |
| Ticketmaster Discovery API | Source of live event data |
| boto3 | Python SDK to interact with AWS S3 |
| schedule | Python library for periodic API fetching |

---

## Project File Structure

```
unievents/
│
├── app.py              # Main Flask application — routes and scheduler
├── events.py           # Fetches events from Ticketmaster API
├── s3_helper.py        # Downloads and uploads event images to S3
├── requirements.txt    # Python dependencies
│
└── templates/
    └── index.html      # HTML page displayed to students
```

---

## Step-by-Step Setup Guide

### Step 1: Get Ticketmaster API Key

1. Go to [https://developer.ticketmaster.com](https://developer.ticketmaster.com)
2. Click **Sign Up** and create a free account
3. After logging in, go to **My Apps** → **Create New App**
4. Copy your **Consumer Key** — this is your API key
5. Test it by visiting in your browser:
   ```
   https://app.ticketmaster.com/discovery/v2/events.json?apikey=YOUR_KEY&size=5
   ```
   You should see live JSON event data.

---

### Step 2: Set Up AWS IAM Role

This role allows your EC2 instances to access S3 without hardcoded passwords.

1. Log in to **AWS Console** → go to **IAM**
2. Click **Roles** → **Create Role**
3. Select **AWS Account**
4. Click **Next** and attach the policy: `AmazonS3FullAccess`
5. Click **Next** and Name the role: `UniEventEC2Role`
6. Click **Create Role**

> This role will be attached to your EC2 instances in Step 5.

---

### Step 3: Create VPC and Subnets

1. Go to **AWS Console** → **VPC** → **Create VPC** and Select **VPC only** option.
   - Name: `UniEventVPC`
   - IPv4 CIDR: `10.0.0.0/16`
   - Click **Create VPC**

2. Create **Public Subnet** (for Load Balancer):
   - Go to **Subnets** → **Create Subnet**
   - VPC: `UniEventVPC`
   - Name: `UniEvent-Public-AZ-a`
   - Availability Zone: `us-east-1a`
   - CIDR: `10.0.1.0/24`
   - 
3. Create **Private Subnet** (for EC2):
   - Name: `UniEvent-Private-AZ-a`
   - Availability Zone: `us-east-1a`
   - CIDR: `10.0.3.0/24`

4. Create an **Internet Gateway**:
   - Go to **Internet Gateways** → **Create Internet Gateway**
   - Name: `UniEventIGW`
   - Attach it to `UniEventVPC`

5. Create and Update the **Route Table** for public and private subnets:
   - Go to **Route Tables** → select create route table
   - Add name `UniEventPriRT` and select the VPC.
   - Then Select Create Route Table.
   - Then associate it with Private subnets.
   - For **Public Subnets**:
   - Add name `UniEventRT` and select the VPC.
   - Go to **edit routes** Add route: Destination `0.0.0.0/0` → Target: `UniEventIGW` 
   - Associate this route table with both public subnets

---

### Step 4: Create S3 Bucket

1. Go to **AWS Console** → **S3** → **Create Bucket**
2. Bucket name: `unievents-images-bucket` *(must be globally unique — add your name if needed)*
3. Region: `us-east-1`
4. **Block all public access**: Keep this ON and check it(our app accesses S3 through IAM role, not publicly)
5. Click **Create Bucket**

6. Update `s3_helper.py` with your bucket name:
   ```python
   S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "unievents-images-bucket") # your actual bucket name
   ```

---

### Step 5: Launch EC2 Instances

1. Go to **AWS Console** → **EC2** → **Launch Instance**
2. Name: `UniEvent-EC2-AZ-a` 
3. AMI: **Ubuntu Server 24.04** 
4. Instance type: `t3.micro` 
5. Key pair: Create or select an existing key pair (save the `.pem` file)
6. Network settings:
   - VPC: `UniEventVPC`
   - Subnet: `UniEvent-Private-AZ-a` 
   - Auto-assign public IP: **Disable** (private subnet — no direct internet)
7. Security Group:
   - Name: `UniEvent-SG` or leave default
   - Inbound rule: Follow Three steps:
   - 1): Select ssh in upper box and My Ip in down box.
   - 2): Select Add Security Group Rule
   - 3): Select**Custom TCP** Allow **port 5000** in upperbox and, custom with source 10.0.0.0/16 in down box.
8. Click **Launch Instance**
9. Network settings:
   - VPC: `UniEventVPC`
   - Name: `Bastian Host`
   - Subnet: `UniEvent-Public-AZ-a` (use AZ-b for the second instance)
   - Auto-assign public IP: **Enable** 
10. Click **Launch Instance**

---

### Step 6: Deploy the Application

Go to connect to instance and SSH into each EC2 instance and run these commands:

```bash
# 1. Connect to EC2 (use a bastion host)
chmod 400 "your key.pem"
ssh -i your-key.pem ec2-user@YOUR_EC2_PRIVATE_IP

# 2. Update the system
sudo apt update -y

# 3. Check Python version
python3 --version

# 4. Clone your GitHub repository
sudo apt install git -y
git --version
git clone https://github.com/YOUR_USERNAME/unievents.git
cd unievents

# 5. Install Python dependencies
pip3 install -r requirements.txt

# 6. Set environment variables
export TICKETMASTER_API_KEY=YOUR_ACTUAL_API_KEY
export S3_BUCKET_NAME=unievents-images-bucket
export AWS_REGION=us-east-1

# 7. Run the application
python3 app.py
```

To keep the app running after you disconnect:

```bash
nohup python3 app.py > app.log 2>&1 &
```

Repeat **Steps 5 and 6** for the second EC2 instance (AZ-b).

---

### Step 7: Set Up Elastic Load Balancer

1. Go to **AWS Console** → **EC2** → **Load Balancers** → **Create Load Balancer**
2. Select **Application Load Balancer**
3. Name: `UniEvent-ALB`
4. Scheme: **Internet-facing**
5. Network mapping:
   - VPC: `UniEventVPC`
   - Availability Zones: Select **both public subnets** (`AZ-a` and `AZ-b`)
6. Security Group: Create new
   - Allow inbound **port 80** (HTTP) from `0.0.0.0/0` (anywhere)
7. Listener: HTTP on port 80

8. Create a **Target Group**:
   - Name: `UniEvent-TG`
   - Target type: Instances
   - Protocol: HTTP, Port: 5000
   - Health check path: `/`
   - Register both EC2 instances as targets

9. Click **Create Load Balancer**

10. Copy the **DNS name** of the Load Balancer — this is the URL students will use to access UniEvent.

---

### Step 8: Test the System

1. Open a browser and go to your Load Balancer DNS name:
   ```
   http://UniEvent-ALB-XXXX.us-east-1.elb.amazonaws.com
   ```

2. You should see the UniEvent homepage with live events from Ticketmaster.

3. **Test fault tolerance** — stop one EC2 instance and verify the site still loads:
   - Go to EC2 → select one instance → Instance State → Stop
   - Refresh the website — it should still work via the second instance

4. **Verify S3 images** — go to your S3 bucket and confirm event images are being uploaded there.

---

## How the Application Works

1. **On startup**, `app.py` immediately calls `fetch_events()` from `events.py`
2. `events.py` sends an HTTPS request to the Ticketmaster API and retrieves event JSON data
3. For each event, `s3_helper.py` downloads the event poster image and uploads it to S3
4. The S3 image URL replaces the original Ticketmaster URL in the event data
5. Events are cached in memory and served to students via the Flask route `/`
6. `index.html` renders the events in a clean card-based grid layout
7. A background thread repeats steps 1–6 every **30 minutes** to keep events fresh
8. The **Load Balancer** receives all student requests and forwards them to whichever EC2 instance is healthy

---

## Security Design

| Security Measure | How It Is Implemented |
|---|---|
| No hardcoded credentials | API key stored as environment variable; S3 accessed via IAM role |
| EC2 not publicly exposed | EC2 instances are in private subnets with no public IP |
| S3 bucket not public | Bucket blocks all public access; only EC2 IAM role can read/write |
| HTTPS for external API | Ticketmaster API calls use HTTPS |
| Security Groups | EC2 only accepts traffic from the Load Balancer, not the internet |

---

## Fault Tolerance

The system continues operating even if one EC2 instance fails because:

- Two EC2 instances run in **separate Availability Zones** (AZ-a and AZ-b)
- The **Elastic Load Balancer** performs regular health checks on both instances
- If one instance fails the health check, the ELB automatically stops sending traffic to it
- All traffic is routed to the remaining healthy instance
- When the failed instance recovers, ELB automatically adds it back to the pool
