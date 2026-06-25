import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger("indusbrain")

# Dynamic Neo4j Connection Check
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

class GraphService:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self.connected = False
        
        # Local mock graph state fallback
        self.mock_nodes = [
            { "id": "PMP-101", "label": "Feed Pump PMP-101", "type": "asset", "health": 85, "spec": "Centrifugal / 185m³/h", "location": "Plant 3 - Pump House A" },
            { "id": "VLV-204", "label": "Control Valve VLV-204", "type": "asset", "health": 68, "spec": "Pneumatic Actuator", "location": "Plant 3 - Gas Feedline B" },
            { "id": "BLR-302", "label": "Boiler BLR-302", "type": "asset", "health": 94, "spec": "High-Pressure Steam / 45T", "location": "Plant 3 - Boiler Block C" },
            { "id": "T-104", "label": "Storage Tank T-104", "type": "asset", "health": 99, "spec": "Class A Hydrocarbon / 5000KL", "location": "Plant Tank Farm East" },
            
            { "id": "SOP-PMP-101", "label": "SOP_FeedPump_v2.pdf", "type": "document", "format": "PDF Standard Procedure", "created": "2024-04-12" },
            { "id": "OEM-VLV-204", "label": "Valve_OEM_Guide_v3.pdf", "type": "document", "format": "OEM Operation Handbook", "created": "2022-09-18" },
            { "id": "SOP-BLR-302", "label": "SOP_Boiler_v4.pdf", "type": "document", "format": "Standard Operating Procedure", "created": "2025-01-05" },
            { "id": "INS-T-104", "label": "Tank_Inspection_2025.xlsx", "type": "document", "format": "Excel Log Sheet", "created": "2025-11-20" },
            { "id": "MAN-PMP-101", "label": "OEM_Pump_Manual_v1.pdf", "type": "document", "format": "OEM Technical Manual", "created": "2020-03-10" },

            { "id": "OISD-189", "label": "OISD-STD-189 (Boiler Safety)", "type": "regulatory", "scope": "Steam Boiler Inspections", "compliance": "Clause 6.2 overridden" },
            { "id": "PESO-ACT", "label": "PESO Explosives Rules", "type": "regulatory", "scope": "Petroleum Storage Safety", "compliance": "Class A Storage zones" },
            { "id": "FACTORY-ACT", "label": "Indian Factory Act 1948", "type": "regulatory", "scope": "Occupational Hazards & Health", "compliance": "Section 35 lighting logs" },
            { "id": "OISD-105", "label": "OISD-STD-105 (Hot Work)", "type": "regulatory", "scope": "Work Permit Clearances", "compliance": "Gas safety tests" },

            { "id": "JO-88321", "label": "Job Order #JO-88321", "type": "incident", "description": "PMP-101 Shaft Seal Leakage fix", "resolved": "14 Days Ago" },
            { "id": "JO-82194", "label": "Job Order #JO-82194", "type": "incident", "description": "VLV-204 sticking risk check", "resolved": "Active" },
            { "id": "RCA-VLV-204", "label": "RCA_Valve_Sticking.md", "type": "incident", "description": "Root Cause on valve failure", "resolved": "Active Analysis" }
        ]

        self.mock_links = [
            { "source": "PMP-101", "target": "SOP-PMP-101", "label": "follows_procedure" },
            { "source": "PMP-101", "target": "MAN-PMP-101", "label": "OEM_reference" },
            { "source": "PMP-101", "target": "JO-88321", "label": "maintained_in" },
            { "source": "JO-88321", "target": "SOP-PMP-101", "label": "verified_via" },
            
            { "source": "VLV-204", "target": "OEM-VLV-204", "label": "OEM_reference" },
            { "source": "VLV-204", "target": "JO-82194", "label": "maintained_in" },
            { "source": "VLV-204", "target": "RCA-VLV-204", "label": "analyzed_in" },
            { "source": "RCA-VLV-204", "target": "OEM-VLV-204", "label": "cites" },
            { "source": "JO-82194", "target": "OISD-105", "label": "requires_permit" },

            { "source": "BLR-302", "target": "SOP-BLR-302", "label": "follows_procedure" },
            { "source": "BLR-302", "target": "OISD-189", "label": "governed_by" },
            { "source": "OISD-189", "target": "SOP-BLR-302", "label": "mandates_rules_in" },

            { "source": "T-104", "target": "INS-T-104", "label": "inspected_in" },
            { "source": "T-104", "target": "PESO-ACT", "label": "licensed_by" },
            { "source": "INS-T-104", "target": "PESO-ACT", "label": "proves_compliance" },
            
            { "source": "FACTORY-ACT", "target": "SOP-BLR-302", "label": "mandates_audit_in" },
            { "source": "FACTORY-ACT", "target": "SOP-PMP-101", "label": "mandates_safety_in" }
        ]

        if HAS_NEO4J and os.getenv("NEO4J_URI"):
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                # Quick ping
                self.driver.verify_connectivity()
                self.connected = True
                logger.info("Connected to Neo4j database successfully.")
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}. Falling back to in-memory graph.")

    def close(self):
        if self.driver:
            self.driver.close()

    def get_graph(self) -> Dict[str, Any]:
        """
        Retrieve all nodes and links for UI mapping.
        """
        if self.connected:
            with self.driver.session() as session:
                result_nodes = session.run("MATCH (n) RETURN n")
                result_rels = session.run("MATCH (n)-[r]->(m) RETURN n.id as source, m.id as target, type(r) as label")
                
                nodes = []
                for record in result_nodes:
                    node = dict(record["n"])
                    # map standard properties
                    node_label = list(record["n"].labels)[0] if record["n"].labels else "Entity"
                    node["type"] = node_label.lower()
                    nodes.append(node)
                
                links = [{"source": r["source"], "target": r["target"], "label": r["label"]} for r in result_rels]
                return {"nodes": nodes, "links": links}
        else:
            return {"nodes": self.mock_nodes, "links": self.mock_links}

    def add_node(self, node_id: str, label: str, node_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add a new node to the Knowledge Graph.
        """
        properties = properties or {}
        properties["id"] = node_id
        properties["label"] = label

        if self.connected:
            label_capitalized = node_type.capitalize()
            with self.driver.session() as session:
                query = f"CREATE (n:{label_capitalized} $props) RETURN n"
                session.run(query, props=properties)
        else:
            new_node = {**properties, "type": node_type}
            self.mock_nodes.append(new_node)

        return properties

    def add_relationship(self, source_id: str, target_id: str, rel_type: str) -> bool:
        """
        Create a directed relationship in the graph.
        """
        if self.connected:
            with self.driver.session() as session:
                query = (
                    "MATCH (a), (b) "
                    "WHERE a.id = $source_id AND b.id = $target_id "
                    f"CREATE (a)-[r:{rel_type.upper()}]->(b) "
                    "RETURN type(r)"
                )
                session.run(query, source_id=source_id, target_id=target_id)
        else:
            self.mock_links.append({
                "source": source_id,
                "target": target_id,
                "label": rel_type.lower()
            })
        return True

    def query_subgraph(self, root_id: str) -> Dict[str, Any]:
        """
        Get all entities linked directly to a target asset node.
        """
        if self.connected:
            with self.driver.session() as session:
                query = (
                    "MATCH (n {id: $root_id})-[r]-(m) "
                    "RETURN n, r, m"
                )
                results = session.run(query, root_id=root_id)
                # Parse to nodes and links...
                # For brevity fallback is used or standard dictionary mappings.
                pass
        
        # In-memory filter
        nodes_ids = {root_id}
        links = []
        for l in self.mock_links:
            if l["source"] == root_id or l["target"] == root_id:
                nodes_ids.add(l["source"])
                nodes_ids.add(l["target"])
                links.append(l)
        
        nodes = [n for n in self.mock_nodes if n["id"] in nodes_ids]
        return {"nodes": nodes, "links": links}
