from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import os
import json
import re
import spacy
from spacy.tokens import Doc
from transformers import pipeline
import graphene
import requests  # For potential schema fetching
from language_model_gateway.gateway.tools.resilient_base_tool import ResilientBaseTool

class GraphqlQueryGeneratorTool(ResilientBaseTool):
    """
    Advanced schema loader for FHIR GraphQL schemas

    Enhanced FHIR GraphQL Query Generator with Dynamic Schema Loading
    """
    nlp_model: Any = field(default_factory=lambda: spacy.load("en_core_web_sm"))
    intent_classifier: Any = field(default_factory=lambda: pipeline("zero-shot-classification"))
    resource_schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """
        Initialize with dynamically loaded schemas
        """
        self.resource_schemas = self.load_schemas_from_github()
        self._setup_intent_classification()

    @staticmethod
    def load_schemas_from_github() -> Dict[str, Dict[str, Any]]:
        """
        Dynamically fetch and parse schemas from GitHub

        Returns:
            Dict of parsed schemas
        """
        base_url = "https://raw.githubusercontent.com/icanbwell/fhir-server/main/src/graphqlv2/schemas/"

        # List of schema files (you might want to dynamically fetch this)
        schema_files = [
            "account.graphql",
            "activity_definition.graphql",
            "adverse_event.graphql",
            "allergy_intolerance.graphql",
            "appointment.graphql",
            "appointment_response.graphql",
            "artifact_assessment.graphql",
            "basic.graphql",
            "binary.graphql",
            "biologically_derived_product.graphql",
            "body_structure.graphql",
            "bundle.graphql",
            "capability_statement.graphql",
            "care_plan.graphql",
            "care_team.graphql",
            "charge_item.graphql",
            "charge_item_definition.graphql",
            "citation.graphql",
            "claim.graphql",
            "claim_response.graphql",
            "clinical_impression.graphql",
            "communication.graphql",
            "communication_request.graphql",
            "compartment_definition.graphql",
            "composition.graphql",
            "concept_map.graphql",
            "condition.graphql",
            "consent.graphql",
            "contract.graphql",
            "coverage.graphql",
            "coverage_eligibility_request.graphql",
            "coverage_eligibility_response.graphql",
            "detected_issue.graphql",
            "device.graphql",
            "device_definition.graphql",
            "device_metric.graphql",
            "device_request.graphql",
            "device_use_statement.graphql",
            "diagnostic_report.graphql",
            "document_manifest.graphql",
            "document_reference.graphql",
            "encounter.graphql",
            "endpoint.graphql",
            "enrollment_request.graphql",
            "enrollment_response.graphql",
            "episode_of_care.graphql",
            "example_scenario.graphql",
            "explanation_of_benefit.graphql",
            "family_member_history.graphql",
            "flag.graphql",
            "goal.graphql",
            "graph_definition.graphql",
            "group.graphql",
            "guidance_response.graphql",
            "healthcare_service.graphql",
            "imaging_study.graphql",
            "immunization.graphql",
            "immunization_evaluation.graphql",
            "immunization_recommendation.graphql",
            "implementation_guide.graphql",
            "ingredient.graphql",
            "insurance_plan.graphql",
            "inventory_report.graphql",
            "invoice.graphql",
            "library.graphql",
            "linkage.graphql",
            "list.graphql",
            "location.graphql",
            "manufactured_item_definition.graphql",
            "measure.graphql",
            "measure_report.graphql",
            "medication.graphql",
            "medication_administration.graphql",
            "medication_dispense.graphql",
            "medication_request.graphql",
            "medication_statement.graphql",
            "medicinal_product_definition.graphql",
            "message_definition.graphql",
            "message_header.graphql",
            "molecular_sequence.graphql",
            "naming_system.graphql",
            "nutrition_intake.graphql",
            "nutrition_order.graphql",
            "observation.graphql",
            "observation_definition.graphql",
            "operation_definition.graphql",
            "operation_outcome.graphql",
            "organization.graphql",
            "organization_affiliation.graphql",
            "pack_age_definition.graphql",
            "patient.graphql",
            "payment_notice.graphql",
            "payment_reconciliation.graphql",
            "permission.graphql",
            "person.graphql",
            "plan_definition.graphql",
            "practitioner.graphql",
            "practitioner_role.graphql",
            "procedure.graphql",
            "provenance.graphql",
            "questionnaire.graphql",
            "questionnaire_response.graphql",
            "regulation.graphql",
            "related_person.graphql",
            "request_group.graphql",
            "research_study.graphql",
            "research_subject.graphql",
            "risk_assessment.graphql",
            "schedule.graphql",
            "search_parameter.graphql",
            "service_request.graphql",
            "slot.graphql",
            "specimen.graphql",
            "specimen_definition.graphql",
            "structure_definition.graphql",
            "subscription.graphql",
            "substance.graphql",
            "substance_definition.graphql",
            "supply_delivery.graphql",
            "supply_request.graphql",
            "task.graphql",
            "terminology_capabilities.graphql",
            "test_report.graphql",
            "test_script.graphql",
            "value_set.graphql",
            "verification_result.graphql",
            "vision_prescription.graphql",
            # Add more schema files
        ]

        schemas = {}

        for schema_file in schema_files:
            try:
                response = requests.get(base_url + schema_file)
                if response.status_code == 200:
                    # Basic schema parsing (simplified)
                    resource_name = schema_file.replace(".graphql", "").upper()
                    schemas[resource_name] = {
                        "fields": self._extract_fields_from_schema(response.text)
                    }
            except Exception as e:
                print(f"Error loading schema {schema_file}: {e}")

        return schemas

    @staticmethod
    def _extract_fields_from_schema(schema_text: str) -> List[str]:
        """
        Extract valid fields from schema text

        Args:
            schema_text (str): Schema file content

        Returns:
            List of valid field names
        """
        # Regex to extract field definitions
        field_patterns = [
            r'(\w+)\s*=\s*graphene\.\w+Field',
            r'def resolve_(\w+)',
            r'class \w+\(graphene\.\w+\):',
        ]

        fields = []
        for pattern in field_patterns:
            fields.extend(re.findall(pattern, schema_text))

        # Clean and deduplicate fields
        return list(set(
            field.lower()
            for field in fields
            if not field.startswith('_') and len(field) > 1
        ))

    def _setup_intent_classification(self):
        """
        Setup advanced intent classification
        """
        self.candidate_labels = list(self.resource_schemas.keys())

    def classify_resource_intent(self, query_text: str) -> str:
        """
        Use zero-shot classification to determine resource type

        Args:
            query_text (str): Natural language query

        Returns:
            str: Predicted resource type
        """
        try:
            classification_result = self.intent_classifier(
                query_text,
                self.candidate_labels,
                multi_label=False
            )

            return classification_result['labels'][0]
        except Exception as e:
            # Fallback mechanism
            print(f"Intent classification failed: {e}")
            return self.candidate_labels[0]  # Default to first resource type

    def parse_natural_language(self, query_text: str) -> Dict[str, Any]:
        """
        Advanced NLP-based query parsing with dynamic schema validation

        Args:
            query_text (str): Natural language query

        Returns:
            Dict with parsed query components
        """
        doc: Doc = self.nlp_model(query_text)

        # Classify resource type
        resource_type = self.classify_resource_intent(query_text)

        intent = {
            "resource_type": resource_type,
            "fields": [],
            "filters": {},
            "sorting": None,
            "pagination": {"limit": 10, "offset": 0}
        }

        # Extract potential fields from available schema
        available_fields = self.resource_schemas.get(resource_type, {}).get('fields', [])

        # Field extraction with schema validation
        potential_fields = [
            chunk.root.lemma_
            for chunk in doc.noun_chunks
            if chunk.root.pos_ in ["NOUN", "PROPN"]
        ]

        # Filter fields based on available schema fields
        intent["fields"] = [
            field for field in potential_fields
            if field in available_fields
        ]

        # Fallback to all available fields if no specific fields found
        if not intent["fields"]:
            intent["fields"] = available_fields[:5]  # Limit to first 5 fields

        # Extract filters from named entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "DATE"]:
                intent["filters"][ent.label_.lower()] = ent.text

        return intent

    def generate_graphql_query(self, query_intent: Dict[str, Any]) -> str:
        """
        Generate sophisticated GraphQL query with schema-validated fields

        Args:
            query_intent (Dict): Parsed query intent

        Returns:
            str: GraphQL query string
        """
        resource_name = query_intent["resource_type"].lower() + "s"

        # Validate and select fields
        available_fields = self.resource_schemas.get(
            query_intent["resource_type"],
            {"fields": ["id"]}
        )["fields"]

        selected_fields = [
                              field for field in query_intent["fields"]
                              if field in available_fields
                          ] or available_fields[:5]

        # Build filters
        filter_str = " ".join([
            f"{k}: {{ eq: \"{v}\" }}"
            for k, v in query_intent["filters"].items()
        ])

        query = f"""
        query {{
            {resource_name}(
                {filter_str}
                _count: {query_intent["pagination"]["limit"]}
                _offset: {query_intent["pagination"]["offset"]}
            ) {{
                entry {{
                    resource {{
                        {" ".join(selected_fields)}
                    }}
                }}
                total
            }}
        }}
        """
        return query

    def process_query(self, query_text: str) -> str:
        """
        Comprehensive query processing pipeline

        Args:
            query_text (str): Natural language query

        Returns:
            str: Generated GraphQL query
        """
        try:
            query_intent = self.parse_natural_language(query_text)
            graphql_query = self.generate_graphql_query(query_intent)
            return graphql_query
        except Exception as e:
            return f"Error generating query: {str(e)}"


# def main():
#     query_generator = GraphqlQueryGeneratorTool()
#
#     test_queries = [
#         "Find all patients with name John",
#         "Get recent observations for diabetes",
#         "List patient details",
#         "Search for medical records",
#         "Retrieve account information"
#     ]
#
#     for query in test_queries:
#         print(f"Natural Language Query: {query}")
#         try:
#             graphql_result = query_generator.process_query(query)
#             print(f"Generated GraphQL Query:\n{graphql_result}\n")
#         except Exception as e:
#             print(f"Query generation error: {e}\n")
#
#
# if __name__ == "__main__":
#     main()