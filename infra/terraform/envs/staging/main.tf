provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# 1. Project Services & APIs
module "project" {
  source     = "../../modules/project"
  project_id = var.project_id
}

# 2. VPC Network & Subnets
module "network" {
  source      = "../../modules/network"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [module.project]
}

# 3. Artifact Registry
module "registry" {
  source     = "../../modules/registry"
  project_id = var.project_id
  region     = var.region

  depends_on = [module.project]
}

# 4. Storage Buckets
module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [module.project]
}

# 5. IAM Service Accounts
module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  environment = var.environment

  depends_on = [module.project]
}

# 6. Cloud SQL PostgreSQL 16 (pgvector with Automated Backups & PITR)
module "sql" {
  source         = "../../modules/sql"
  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  vpc_id         = module.network.vpc_id
  psa_connection = module.network.psa_connection
  db_password    = var.db_password
}

# 7. Memorystore Redis (In-transit TLS & Auth)
module "redis" {
  source         = "../../modules/redis"
  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  vpc_id         = module.network.vpc_id
  psa_connection = module.network.psa_connection
}

# 8. Vertex AI Model Endpoint Shell
module "vertex_endpoint" {
  source      = "../../modules/vertex_endpoint"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [module.project]
}

# 9. Binary Authorization (Enforcing Cosign Signatures)
module "binauthz" {
  source                = "../../modules/binauthz"
  project_id            = var.project_id
  environment           = var.environment
  enforce               = var.enable_binary_authorization
  service_account_email = module.iam.sa_api_email

  depends_on = [module.project]
}

# 10. Cloud Run API Gateway (Binary Auth & Health Probes)
module "cloud_run_service" {
  source                      = "../../modules/cloud_run_service"
  project_id                  = var.project_id
  region                      = var.region
  environment                 = var.environment
  image                       = var.api_image
  service_account_email       = module.iam.sa_api_email
  vpc_connector_id            = module.network.connector_id
  enable_binary_authorization = var.enable_binary_authorization
  min_instance_count          = 1
  max_instance_count          = 10

  env_vars = {
    CC_POSTGRES_URL = "postgresql+asyncpg://cc_app:${var.db_password}@${module.sql.private_ip_address}:5432/cc_platform"
    CC_REDIS_URL    = module.redis.redis_url
    CC_GCS_BUCKET   = module.storage.models_bucket
  }

  depends_on = [module.sql, module.redis, module.binauthz]
}

# 11. Cloud Scheduler (Monthly Intent Retraining, Weekly KB Sync, Nightly Eval)
module "scheduler" {
  source                = "../../modules/scheduler"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = module.iam.sa_pipeline_email
  api_gateway_url       = module.cloud_run_service.uri

  depends_on = [module.cloud_run_service]
}

# 12. Firebase Hosting Site
module "firebase" {
  source     = "../../modules/firebase"
  project_id = var.project_id

  depends_on = [module.project]
}

# 13. Load Balancer with Cloud Armor and IAP
module "lb_armor_iap" {
  source                 = "../../modules/lb_armor_iap"
  project_id             = var.project_id
  region                 = var.region
  environment            = var.environment
  cloud_run_service_name = module.cloud_run_service.service_name
  enable_iap             = false
}
