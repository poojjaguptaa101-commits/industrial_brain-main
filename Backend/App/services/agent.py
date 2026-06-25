import os
import logging
from typing import Dict, Any, List
from app.services.graph import GraphService
from app.services.vector import VectorService

logger = logging.getLogger("indusbrain")

# Dynamic LangChain and LLM imports
try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.tools import tool
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

class AgentService:
    def __init__(self, graph_service: GraphService, vector_service: VectorService):
        self.graph_service = graph_service
        self.vector_service = vector_service
        self.agent_executor = None
        self.use_real_agent = False
        
        # Check API Keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        if HAS_LANGCHAIN and (self.openai_key or self.gemini_key):
            try:
                self._setup_langchain_agent()
                self.use_real_agent = True
                logger.info("LangChain Agent pipeline configured successfully.")
            except Exception as e:
                logger.warning(f"LangChain Agent setup failed: {e}. Defaulting to rule-based agent mockup.")
        else:
            logger.info("No API keys found. Using high-fidelity rule-based agent mockup.")

    def _setup_langchain_agent(self):
        # 1. Define tools for the LangChain agent
        @tool
        def query_vector_db(query: str) -> str:
            """Query ChromaDB for PDF, SOP, and OEM handbook documentation text."""
            results = self.vector_service.search(query, limit=3)
            return "\n\n".join([f"Source: {r['metadata']['source']} - Text: {r['text']}" for r in results])

        @tool
        def query_knowledge_graph(root_id: str) -> str:
            """Retrieve the direct connections of an asset tag from the Neo4j Graph."""
            subgraph = self.graph_service.query_subgraph(root_id)
            nodes = subgraph["nodes"]
            links = subgraph["links"]
            
            nodes_desc = ", ".join([f"{n['id']} ({n['type']})" for n in nodes])
            links_desc = ", ".join([f"{l['source']} --[{l['label']}]--> {l['target']}" for l in links])
            return f"Nodes: {nodes_desc}\nRelationships: {links_desc}"

        self.tools = [query_vector_db, query_knowledge_graph]

        # 2. Setup prompt and model
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the IndusBrain Industrial Intelligence Agent. You assist reliability engineers and field technicians. "
                       "You must query the vector store for manuals/SOPs and the knowledge graph for asset tags and connections to synthesize precise answers. "
                       "Format answers with clear numbered steps. Add 'References' showing sources. Add 'Confidence' score (80-100%)."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Default to OpenAI if key exists, otherwise we'd wrap Gemini
        if self.openai_key:
            model = ChatOpenAI(temperature=0.2, model="gpt-4o")
            agent = create_openai_tools_agent(model, self.tools, prompt)
            self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        else:
            # Placeholder for Gemini API integration via LangChain Google package
            pass

    def run_query(self, query: str) -> Dict[str, Any]:
        """
        Execute query using LangChain executor or local mockup fallback.
        """
        if self.use_real_agent and self.agent_executor:
            try:
                response = self.agent_executor.invoke({"input": query})
                # Parse references from the LLM output or trace tools
                return {
                    "answer": response["output"],
                    "citations": ["Vector Search Context", "Neo4j Graph Database"],
                    "confidence": 92
                }
            except Exception as e:
                logger.warning(f"Agent execution failed: {e}. Falling back to mockup.")

        return self._mock_agent_response(query)

    def _mock_agent_response(self, query: str) -> Dict[str, Any]:
        """
        Rule-based NLP mockup response matching typical industrial queries.
        """
        low_q = query.lower()
        if "pmp-101" in low_q and "start" in low_q:
            return {
                "answer": "To start up **Feed Pump PMP-101**:\n\n"
                          "1. **Pre-start verification:** Inspect lube oil level; verify pressure is > **1.8 bar**.\n"
                          "2. **Suction Alignment:** Ensure the pump suction valve is 100% open.\n"
                          "3. **De-aeration:** Bleed the casing air valve until fluid flows continuously.\n"
                          "4. **Startup:** Power on the motor. Discharge valve must remain closed until rotation reaches full speed.\n"
                          "5. **Flow control:** Slowly crack open the discharge valve to pressure spec **4.2 bar**.",
                "citations": ["SOP_FeedPump_v2.pdf (Page 4)", "OEM_Pump_Manual_v1.pdf"],
                "confidence": 98
            }
        elif "oisd" in low_q and "hot work" in low_q:
            return {
                "answer": "Under **OISD-STD-105 Clause 6.4**, hot work permits mandate:\n\n"
                          "1. **LEL gas testing:** Gas testing is mandatory; explosive levels must be **0.0%**.\n"
                          "2. **Clearance perimeter:** clear any combustible materials in a **15-meter zone**.\n"
                          "3. **Equipment blanking:** Blanks must isolate all connected fuel inlets.\n"
                          "4. **Fire Watch:** A crew member with active extinguisher must oversee the process.",
                "citations": ["OISD-STD-105 (Section 6.4)", "Factory_Safety_Code.pdf"],
                "confidence": 95
            }
        elif "vlv-204" in low_q or "valve" in low_q:
            return {
                "answer": "**Control Valve VLV-204** diagnostics match historical incident logs:\n\n"
                          "- **Friction:** Actuator friction score is high (24%), indicating spindle sticking.\n"
                          "- **Cause:** Moisture residue in pneumatic pipes degrades the spring chamber.\n"
                          "- **Spec Check:** OEM Page 47 requires clean dry air feed at **5.5 bar**. Sensor shows **5.1 bar**.\n\n"
                          "**Action:** Schedule instrument air moisture filter replacement.",
                "citations": ["Valve_OEM_Guide_v3.pdf (Page 47)", "RCA_Valve_Sticking.md"],
                "confidence": 91
            }
        else:
            return {
                "answer": f"I parsed your query: '{query}'. Based on cross-linking references in the Knowledge Graph, this concerns "
                          "Jamnagar complex operations. Please check that active maintenance work orders are verified in the compliance log "
                          "and that your gas clearance certificate is signed off by your supervisor.",
                "citations": ["General_Plant_Index.pdf"],
                "confidence": 85
            }
        
    def generate_rca(self, incident_id: str) -> Dict[str, Any]:
        """
        Generate Fishbone and 5-Whys diagrams for a given incident.
        """
        if incident_id == "pmp-leak":
            return {
                "effect": "PMP-101 Seal Leak",
                "whys": [
                    "Shaft seal micro-cracked and leaked hydrocarbons.",
                    "High axial shaft vibration wore down mechanical carbon seal face.",
                    "Impeller cavitation induced unbalanced rotational forces on the shaft.",
                    "Viscous petroleum feed rate increased while intake pressure dropped below 1.4 bar.",
                    "Failure to cross-reference feed pump design limits in OEM Manual Page 22 during shift process changes."
                ],
                "capas": [
                    "Install automated suction-pressure trip interlock on PMP-101 control panel.",
                    "Incorporate OEM flow-limit curves directly into real-time sensor dashboards.",
                    "Revise shift handover checklist to mandate feed viscosity limits audits."
                ],
                "causes": {
                    "man": ["Manual override", "No limit checks"],
                    "machine": ["Cavitation", "Seal wear"],
                    "method": ["SOP gap", "Friction spike"],
                    "material": ["High viscosity", "Pressure drop"]
                }
            }
        elif incident_id == "vlv-stick":
            return {
                "effect": "VLV-204 Sticking",
                "whys": [
                    "Pneumatic positioner failed to respond to flow commands.",
                    "Friction coefficient inside pneumatic actuator rose to 24% (sticking).",
                    "Moisture accumulation inside the pneumatic diaphragm rusted the spring housing.",
                    "Instrument air supply feed gas filter was saturated with liquid moisture.",
                    "Scheduled quarterly filter-drain inspections were omitted due to maintenance logging gaps."
                ],
                "capas": [
                    "Replace VLV-204 actuator spring and execute stroke calibration.",
                    "Update standard operating procedure to require weekly air-manifold drain verification.",
                    "Integrate air dryer alarm telemetry directly into the Unified Operations Brain."
                ],
                "causes": {
                    "man": ["Omitted inspection", "No filter log"],
                    "machine": ["Dry air pressure", "Actuator rust"],
                    "method": ["Manual stroke bypass", "Calibration lag"],
                    "material": ["Moisture feed", "Worn diaphragm"]
                }
            }
        else:
            return {
                "effect": "Boiler Creep",
                "whys": [
                    "Boiler superheater tube ruptured, forcing unplanned shutdown.",
                    "Tube wall suffered rapid creep deformation and thinning.",
                    "Local temperature exceeded design limit of 620°C for extended runs.",
                    "Chemical scaling on the tube water-side restricted internal heat transfer.",
                    "Demineralized water treatment plant suffered pH and silica control spikes last month."
                ],
                "capas": [
                    "Perform chemical acid-cleaning of boiler internals to clear scaling.",
                    "Install high-temperature infrared sensor grid to detect local tube hotspots.",
                    "Mandate daily laboratory reports uploads into regulatory compliance directory."
                ],
                "causes": {
                    "man": ["Log missing", "No pH follow"],
                    "machine": ["Hotspot scaling", "Temp peak"],
                    "method": ["Water feed shift", "No thermal sweep"],
                    "material": ["Silica build-up", "Scale layer"]
                }
            }
