project_id                  = "sample-project-prod"
region                      = "us-central1"
environment                 = "prod"
api_image                   = "us-central1-docker.pkg.dev/sample-project-prod/cc-platform-docker/api:latest"
enable_binary_authorization = true
enable_iap                  = true
canary_percent              = 0
canary_revision             = null
