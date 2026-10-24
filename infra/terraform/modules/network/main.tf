# 1. VPC Network
resource "google_compute_network" "vpc" {
  name                    = "cc-vpc-${var.environment}"
  project                 = var.project_id
  auto_create_subnetworks = false
}

# 2. Main Regional Subnet (with Private Google Access)
resource "google_compute_subnetwork" "subnet" {
  name                     = "cc-subnet-${var.environment}"
  project                  = var.project_id
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true
}

# 3. Cloud Router & Cloud NAT for Outbound Internet Egress
resource "google_compute_router" "router" {
  name    = "cc-router-${var.environment}"
  project = var.project_id
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "cc-nat-${var.environment}"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.router.name
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# 4. Serverless VPC Access Connector for Cloud Run Egress
resource "google_vpc_access_connector" "connector" {
  name          = "cc-conn-${var.environment}"
  project       = var.project_id
  region        = var.region
  ip_cidr_range = var.connector_cidr
  network       = google_compute_network.vpc.name
  min_instances = 2
  max_instances = 5
}

# 5. Private Service Access (PSA) for Cloud SQL & Redis Peering
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "cc-psa-${var.environment}"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}
