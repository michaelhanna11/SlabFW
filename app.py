import streamlit as st
import pandas as pd

def calculate_concrete_load(thickness, reinforcement_percentage):
    """Calculate G_c in kN/m² based on concrete thickness and reinforcement percentage."""
    base_density = 24.50  # kN/m³
    reinforcement_load = 0.5 * reinforcement_percentage  # kN/m²
    G_c = base_density * thickness + reinforcement_load * thickness
    return G_c

def compute_combinations(G_f, G_c, Q_w, Q_m, stage):
    """Compute simplified load combinations for slab formwork design."""
    combinations = []
    
    if stage == "1":  # Prior to concrete placement
        comb_1 = 1.35 * G_f  # Dead load only
        comb_2 = 1.2 * G_f + 1.5 * Q_w + 1.5 * Q_m  # Construction loads
        combinations = [comb_1, comb_2]
    
    elif stage == "2":  # During concrete placement
        comb_3 = 1.35 * G_f + 1.35 * G_c  # Dead loads
        comb_4 = 1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m  # All loads
        combinations = [comb_3, comb_4]
    
    elif stage == "3":  # After concrete placement
        comb_5 = 1.35 * G_f + 1.35 * G_c  # Dead loads
        comb_6 = 1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m  # Workers + materials
        combinations = [comb_5, comb_6]
    
    return combinations

def main():
    st.set_page_config(page_title="Slab Load Calculator", layout="wide")
    st.title("Slab Load Calculator to AS 3610.2")
    
    with st.sidebar:
        st.header("Project Details")
        project_name = st.text_input("Project Name", "My Project")
        
        st.header("Material Properties")
        thickness = st.number_input("Concrete thickness (m)", 
                                  min_value=0.1, max_value=1.5, 
                                  value=0.2, step=0.05)
        reinforcement = st.number_input("Reinforcement percentage (%)", 
                                      min_value=0.0, max_value=5.0, 
                                      value=1.0, step=0.5)
        G_f = st.number_input("Formwork self-weight (kPa)", 
                             min_value=0.1, value=0.5, step=0.1)
        
        st.header("Stage 1: Before Concrete Placement")
        Q_w1 = st.number_input("Workers & equipment (kPa) - Stage 1", 
                              min_value=0.5, value=1.0, step=0.1)
        Q_m1 = st.number_input("Material storage (kPa) - Stage 1", 
                              min_value=0.0, value=0.0, step=0.1)
        
        st.header("Stage 2: During Concrete Placement")
        Q_w2 = st.number_input("Workers & equipment (kPa) - Stage 2", 
                              min_value=0.5, value=2.0, step=0.1)
        Q_m2 = st.number_input("Material storage (kPa) - Stage 2", 
                              min_value=0.0, value=2.5, step=0.1)
        
        st.header("Stage 3: After Concrete Placement")
        Q_w3 = st.number_input("Workers & equipment (kPa) - Stage 3", 
                              min_value=0.5, value=1.0, step=0.1)
        Q_m3 = st.number_input("Material storage (kPa) - Stage 3", 
                              min_value=0.0, value=0.0, step=0.1)
    
    # Calculate concrete load
    G_c = calculate_concrete_load(thickness, reinforcement)
    
    # Calculate load combinations for all stages
    results = {
        "1": {
            "description": "Prior to concrete placement",
            "Q_w": Q_w1,
            "Q_m": Q_m1,
            "combinations": compute_combinations(G_f, G_c, Q_w1, Q_m1, "1")
        },
        "2": {
            "description": "During concrete placement",
            "Q_w": Q_w2,
            "Q_m": Q_m2,
            "combinations": compute_combinations(G_f, G_c, Q_w2, Q_m2, "2")
        },
        "3": {
            "description": "After concrete placement",
            "Q_w": Q_w3,
            "Q_m": Q_m3,
            "combinations": compute_combinations(G_f, G_c, Q_w3, Q_m3, "3")
        }
    }
    
    # Find maximum load
    max_load = max(max(stage["combinations"]) for stage in results.values())
    critical_stage = next(k for k,v in results.items() if max(v["combinations"]) == max_load)
    
    # Display results
    st.header("Results Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Concrete Load (G_c)", f"{G_c:.2f} kPa")
    col2.metric("Maximum Design Load", f"{max_load:.2f} kPa")
    col3.metric("Critical Stage", f"Stage {critical_stage}")
    
    st.header("Detailed Load Combinations")
    for stage, data in results.items():
        with st.expander(f"Stage {stage}: {data['description']}"):
            st.caption(f"Workers & equipment: {data['Q_w']} kPa | Material storage: {data['Q_m']} kPa")
            
            df = pd.DataFrame({
                "Case": [f"Combination {i+1}" for i in range(len(data['combinations']))],
                "Load (kPa)": data['combinations'],
                "Components": get_components_description(stage, G_f, G_c, data['Q_w'], data['Q_m'])
            })
            st.dataframe(df.style.format({"Load (kPa)": "{:.2f}"}), 
                        hide_index=True, 
                        use_container_width=True)
    
    # Design recommendation
    st.header("Design Recommendation")
    st.success(f"""
    **Design load = {max_load:.2f} kPa** (from Stage {critical_stage})
    """)
    st.caption("Note: Calculated per AS 3610.2 strength limit state combinations for vertical loads")

def get_components_description(stage, G_f, G_c, Q_w, Q_m):
    """Return description of load components for each combination."""
    if stage == "1":
        return [
            "1.35 × G_f",
            "1.2 × G_f + 1.5 × Q_w + 1.5 × Q_m"
        ]
    elif stage == "2":
        return [
            "1.35 × G_f + 1.35 × G_c",
            "1.2 × G_f + 1.2 × G_c + 1.5 × Q_w + 1.5 × Q_m"
        ]
    elif stage == "3":
        return [
            "1.35 × G_f + 1.35 × G_c",
            "1.2 × G_f + 1.2 × G_c + 1.5 × Q_w + 1.5 × Q_m"
        ]

if __name__ == "__main__":
    main()
