"""
Main Entry Point for Pipeline 2: Surgical Template Injection
Generates EY-branded presentations from project documentation.
"""
import os
import sys
import json
import importlib
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

# Load environment variables
load_dotenv()

# CRITICAL: Force reload of modified modules to ensure defensive fixes are active
# (Prevents Python module caching from using old code)
print("[RELOAD] Forcing reload of modified pipeline modules...")
for mod_name in [
    'src.nodes.pipeline_2_generation.injector',
    'src.nodes.pipeline_2_generation.beautifier',
    'src.nodes.pipeline_2_generation.writer'
]:
    if mod_name in sys.modules:
        print(f"  [RELOAD] Reloading: {mod_name}")
        importlib.reload(sys.modules[mod_name])
    else:
        print(f"  [OK] Fresh load: {mod_name}")

from src.core.graph_pipeline2 import create_pipeline2_graph
from src.utils.registry_helper import load_all_registries
from src.core.state import PPTState
 
def run_pipeline_2(raw_documentation: str, primary_master: str = "template2.pptx"):
    """
    Execute Pipeline 2 to generate a complete EY presentation.
    """
    # Load all template registries (Unified Registry)
    combined_registry = load_all_registries()
    
    if not combined_registry:
        print("Error: No EY templates found in registry. Run Pipeline 1 first!")
        return
        
    primary_master_name = os.path.basename(primary_master)
    primary_registry_key = os.path.splitext(primary_master_name)[0]
    
    # We strictly use the registry for the PRIMARY MASTER
    if primary_registry_key not in combined_registry:
        print(f"Error: Registry for {primary_master_name} not found in data/registry/")
        return
        
    target_registry = combined_registry[primary_registry_key]
    
    # Setup initial state
    initial_state = PPTState(
        raw_docs=raw_documentation,
        primary_master_path=f"data/templates/{primary_master}",
        registry=target_registry,
        content_map=None,
        slide_plans=[],
        manifest=[],
        final_file_path=None,
        validation_errors=[],
        thread_id="ey_gen_001",
        current_step="start"
    )
    
    # Initialize and run the graph
    app = create_pipeline2_graph()
    
    print(f"--- 🚀 Starting Pipeline 2 for EY: {primary_master_name} ---")
    config = {"configurable": {"thread_id": "ey_gen_001"}}
    
    try:
        config_obj = RunnableConfig(configurable={"thread_id": "ey_gen_001"})
        final_state = app.invoke(initial_state, config=config_obj)
        if final_state.get("final_file_path"):
            print(f"\n--- ✅ Success! EY Presentation created: {final_state['final_file_path']} ---")
        else:
            print("\n--- ❌ Pipeline failed to generate presentation ---")
    except Exception as e:
        print(f"\n--- ❌ Pipeline error: {e} ---")
        raise
 
if __name__ == "__main__":
    # --- FEEDING CONTENT ---
    # Paste your EY project documentation or requirements here.
    ey_documentation = """
   Ernst & Young (EY) is one of the world’s “Big Four” accounting firms, widely recognized for its robust audit and assurance services. EY auditing revolves around providing independent, high‑quality examinations of financial statements to promote transparency, build stakeholder trust, and support strong corporate governance. The firm’s auditing methodologies combine deep industry knowledge, advanced technology, and strict professional standards to deliver reliable insights that help organizations navigate an increasingly complex business environment.
At its core, EY's audit practice focuses on verifying whether a company’s financial statements present a true and fair view of its financial position and performance. This includes assessing revenue recognition, expense classification, asset valuation, liabilities, internal controls, and compliance with relevant accounting frameworks such as International Financial Reporting Standards (IFRS), Generally Accepted Accounting Principles (GAAP), and country‑specific regulations. EY auditors apply a risk‑based approach, meaning they identify the most significant areas of risk within a business and tailor their audit procedures accordingly. This not only improves efficiency but also ensures that critical issues receive the highest level of scrutiny.
A key strength of EY auditing is the integration of technology. Through platforms like EY Helix and other data‑analytics tools, auditors can analyze vast amounts of transactional data quickly and accurately. This allows them to identify unusual patterns, detect irregularities, and gain a deeper understanding of business processes. Technology‑enabled auditing enhances audit quality while reducing the manual effort traditionally required in sampling and testing. It also enables auditors to provide additional insights to management, helping them improve operational efficiency and risk management.
Another hallmark of EY’s audit practice is its emphasis on independence and ethical conduct. EY adheres to global professional standards, including those set by the International Ethics Standards Board for Accountants (IESBA). Auditors are required to maintain objectivity, avoid conflicts of interest, and uphold confidentiality. The firm regularly conducts internal quality reviews, ongoing training programs, and external inspections to ensure compliance with rigorous standards. Such measures reinforce the reliability of EY’s audit opinions and contribute to the credibility of financial markets.
EY’s global presence also enhances its audit capabilities. With teams operating across more than 150 countries, the firm is well‑equipped to handle multinational clients with complex structures. Cross‑border coordination ensures consistent audit methodologies, timely communication, and a deep understanding of diverse regulatory requirements. This global integration supports large corporations in meeting both local and international reporting obligations.
In addition to traditional financial audits, EY provides specialized assurance services, including sustainability reporting, IT audits, internal control evaluations, and cybersecurity assessments. As businesses increasingly focus on environmental, social, and governance (ESG) factors, EY’s role in validating non‑financial disclosures is becoming more significant. The firm helps clients build trust with stakeholders by ensuring transparency not just in financial performance but also in broader business practices.
Overall, EY auditing stands out for its strong commitment to quality, technological innovation, global reach, and ethical integrity. By delivering reliable and insightful audits, EY plays a crucial role in strengthening the financial ecosystem and supporting informed decision‑making for investors, regulators, and business leaders alike.
    """
    
    # Use your official EY master template name here
    run_pipeline_2(ey_documentation, primary_master="template2.pptx")