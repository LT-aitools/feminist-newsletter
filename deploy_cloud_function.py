#!/usr/bin/env python3
"""
Deploy Cloud Function with service account authentication.
"""
import subprocess
import logging

def deploy_cloud_function():
    """Deploy the Cloud Function with service account authentication."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=== DEPLOYING CLOUD FUNCTION ===")
    
    # Set the project
    project_id = "womens-rights-calendar"
    
    # Deploy using 1st gen Cloud Functions as recommended in README
    # Remove OAuth credentials and use service account authentication
    cmd = [
        "gcloud", "functions", "deploy", "newsletter-processor",
        "--runtime=python311",
        "--trigger-http",
        "--allow-unauthenticated",
        "--memory=512MB",
        "--timeout=540s",
        "--source=.",
        "--entry-point=newsletter_processor",
        "--region=us-central1",
        "--project=" + project_id,
        "--no-gen2",  # Use 1st gen as recommended
        "--service-account=vision-api-access@womens-rights-calendar.iam.gserviceaccount.com",  # Specify correct service account
        "--set-env-vars=GCP_PROJECT=" + project_id  # Set only the needed env var, clears all others
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("✅ Cloud Function deployed successfully!")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Deployment failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    deploy_cloud_function() 