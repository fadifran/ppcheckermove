# PostPros Job Checker

A Streamlit-based internal tool for Post Pros to compare mailing list data between Accuzip files and client files.

## Features

- **File Upload & Processing**: Support for CSV and ZIP files containing CSVs
- **Dataset Comparison**: Compare Accuzip records against client files with configurable column mapping
- **Seed Record Search**: Search for specific records across multiple fields
- **Postal Rate Statistics**: Calculate and display postal rate metrics
- **IMB Validation**: Validate Intelligent Mail Barcode codes and compare decoded ZIP codes
- **Google Street View**: Display Street View images for address verification

## Project Structure

```
postpros-job-checker/
├── main.py                    # Main Streamlit application
├── config.py                  # Configuration constants
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project metadata
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   └── style.css             # Custom CSS styles
└── utils/
    ├── __init__.py           # Package initialization
    ├── file_processor.py     # CSV/ZIP file handling
    ├── data_validator.py     # Dataset comparison logic
    ├── imb_validator.py      # IMB barcode validation
    ├── streetview_processor.py # Google Street View integration
    ├── usps_imb_decoder.py   # USPS barcode decoding
    └── html_utils.py         # Safe HTML rendering utilities
```

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/fadifran/PostPros-Job-Checker.git
   cd PostPros-Job-Checker
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional, for Street View)
   ```bash
   export GOOGLE_MAPS_API_KEY="your-api-key-here"
   ```

5. **Run the application**
   ```bash
   streamlit run main.py
   ```

6. **Open in browser**
   Navigate to `http://localhost:8501`

---

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - Free)

The easiest way to deploy a Streamlit app for free.

#### Steps:

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"**

4. **Configure deployment:**
   - Repository: `fadifran/PostPros-Job-Checker`
   - Branch: `main`
   - Main file path: `main.py`

5. **Add secrets** (for Google Street View):
   - Click "Advanced settings"
   - Add to Secrets:
     ```toml
     GOOGLE_MAPS_API_KEY = "your-api-key-here"
     ```

6. **Click "Deploy"**

Your app will be available at: `https://your-app-name.streamlit.app`

---

### Option 2: Replit

Good for quick prototyping and sharing.

#### Steps:

1. **Go to [replit.com](https://replit.com)** and create an account

2. **Create a new Repl:**
   - Click "Create Repl"
   - Select "Import from GitHub"
   - Paste: `https://github.com/fadifran/PostPros-Job-Checker`

3. **Configure the Repl:**
   - Create a `.replit` file:
     ```toml
     run = "streamlit run main.py --server.port 5000 --server.address 0.0.0.0"
     
     [nix]
     channel = "stable-23_11"
     
     [deployment]
     run = ["sh", "-c", "streamlit run main.py --server.port 5000 --server.address 0.0.0.0"]
     ```

4. **Add Secrets:**
   - Go to "Secrets" tab (lock icon)
   - Add: `GOOGLE_MAPS_API_KEY` = `your-api-key`

5. **Click "Run"**

---

### Option 3: Railway

Simple deployment with automatic builds.

#### Steps:

1. **Go to [railway.app](https://railway.app)** and sign up

2. **Create new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select `PostPros-Job-Checker` repository

3. **Configure environment:**
   - Go to "Variables" tab
   - Add: `GOOGLE_MAPS_API_KEY` = `your-api-key`

4. **Add start command:**
   - Go to Settings → Deploy
   - Set start command:
     ```bash
     streamlit run main.py --server.port $PORT --server.address 0.0.0.0
     ```

5. **Deploy** - Railway will automatically build and deploy

---

### Option 4: Render

Free tier available with automatic SSL.

#### Steps:

1. **Go to [render.com](https://render.com)** and create an account

2. **Create a new Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository

3. **Configure the service:**
   - **Name**: `postpros-job-checker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run main.py --server.port $PORT --server.address 0.0.0.0`

4. **Add environment variables:**
   - `GOOGLE_MAPS_API_KEY` = `your-api-key`

5. **Click "Create Web Service"**

---

### Option 5: Docker (Self-Hosted)

For deployment on your own servers or cloud VMs.

#### Dockerfile

Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Build and Run

```bash
# Build the image
docker build -t postpros-job-checker .

# Run the container
docker run -d \
  -p 8501:8501 \
  -e GOOGLE_MAPS_API_KEY="your-api-key" \
  --name postpros \
  postpros-job-checker
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

---

### Option 6: AWS (Production)

For enterprise-grade deployment.

#### Using AWS App Runner

1. **Push Docker image to ECR:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

   # Create repository
   aws ecr create-repository --repository-name postpros-job-checker

   # Build and push
   docker build -t postpros-job-checker .
   docker tag postpros-job-checker:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/postpros-job-checker:latest
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/postpros-job-checker:latest
   ```

2. **Create App Runner service:**
   - Go to AWS Console → App Runner
   - Create service from ECR image
   - Configure port: 8501
   - Add environment variables

#### Using EC2

1. Launch an EC2 instance (t2.micro for testing, t2.small+ for production)
2. SSH into the instance
3. Install Docker:
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```
4. Run the container as shown in Docker section

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | No | Google Maps API key for Street View images |

### Getting a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the "Street View Static API"
4. Go to Credentials → Create Credentials → API Key
5. (Recommended) Restrict the API key:
   - Application restrictions: HTTP referrers
   - API restrictions: Street View Static API only

---

## Security Notes

⚠️ **Important Security Considerations:**

1. **API Key Protection**: The Google Maps API key is exposed in client-side HTML when using Street View. For production:
   - Restrict your API key by HTTP referrer in Google Cloud Console
   - Consider implementing a server-side proxy for Street View requests
   - Set usage quotas to prevent unexpected charges

2. **File Uploads**: The application processes user-uploaded files. Ensure:
   - The deployment platform has appropriate file size limits
   - Files are processed in memory and not persisted unnecessarily

3. **Access Control**: This is an internal tool. Consider:
   - Adding authentication (Streamlit has built-in auth on Community Cloud)
   - Using a private network or VPN for self-hosted deployments
   - Implementing IP whitelisting

---

## Troubleshooting

### Common Issues

**App won't start:**
- Check Python version (requires 3.10+)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check for port conflicts: `lsof -i :8501`

**File upload fails:**
- Check file size limits (Streamlit default: 200MB)
- Ensure files are valid CSV or ZIP containing CSVs
- Check file encoding (UTF-8 recommended)

**Street View not loading:**
- Verify GOOGLE_MAPS_API_KEY is set correctly
- Check API key restrictions in Google Cloud Console
- Ensure Street View Static API is enabled

**IMB validation errors:**
- Verify IMB codes are 65 characters
- Check for valid characters (A, D, T, F only)
- Ensure correct column selection

---

## Development

### Running Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=.
```

### Code Formatting

```bash
pip install black
black . --line-length 100
```

### Type Checking

```bash
pip install mypy
mypy . --ignore-missing-imports
```

---

## License

Proprietary - For Post Pros Internal Use Only

## Support

For issues or questions, contact the Post Pros development team.
