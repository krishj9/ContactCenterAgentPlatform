resource "google_vertex_ai_endpoint" "endpoint" {
  name         = "intent-endpoint-${var.environment}"
  display_name = "Intent Classifier Endpoint (${var.environment})"
  description  = "Vertex AI Endpoint for fine-tuned Gemma 3 1B LoRA intent classification"
  location     = var.region
  project      = var.project_id
  network      = var.network_id
}
