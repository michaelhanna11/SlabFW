import streamlit as st
import pandas as pd
from enum import Enum

# ========================
# ENUM DEFINITIONS
# ========================
class FormworkSystem(Enum):
    PERI_SKYDECK = "PERI Skydeck"
    GRIDFLEX = "Gridflex"
    ALPHADECK = "Alphadeck"

class SkydeckSupportType(Enum):
    NO_SUPPORT = "No mid-support"
    BEAM_SUPPORT = "Mid support under beam"
    PANEL_SUPPORT = "Mid support under panel"
    BOTH_SUPPORT = "Mid support under both panel and beam"

# ========================
# LOAD CALCULATOR MODULE
# ========================
def calculate_concrete_load(thickness, reinforcement_percentage):
    """Calculate G_c in kN/m² based on concrete thickness and reinforcement percentage."""
    base_density = 24.50  # kN/m³
    reinforcement_load = 0.5 * reinforcement_percentage  # kN/m²
    return base_density * thickness + reinforcement_load * thickness

def compute_combinations(G_f, G_c, Q_w, Q_m, stage):
    """Compute load combinations with unanticipated load factor (γ_d = 1.3)"""
    gamma_d = 1.3  # Unanticipated load factor
    
    if stage == "1":  # Prior to concrete placement
        return [
            1.35 * G_f,  # No γ_d
            gamma_d * (1.2 * G_f + 1.5 * Q_w + 1.5 * Q_m)
        ]
    elif stage == "2":  # During concrete placement
        return [
            gamma_d * (1.35 * G_f + 1.35 * G_c),
            gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m)
        ]
    elif stage == "3":  # After concrete placement
        return [
            gamma_d * (1.35 * G_f + 1.35 * G_c),
            gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m)
        ]

def load_calculator_module():
    st.header("AS 3610.2 Load Calculator")
    
    with st.sidebar:
        st.subheader("Project Details")
        project_name = st.text_input("Project Name", "My Project")
        
        st.subheader("Material Properties")
        thickness = st.number_input("Concrete thickness (m)", 
                                  min_value=0.05, max_value=1.5, 
                                  value=0.2, step=0.05)
        reinforcement = st.number_input("Reinforcement percentage (%)", 
                                      min_value=0.0, max_value=5.0, 
                                      value=1.0, step=0.5)
        G_f = st.number_input("Formwork self-weight (kPa)", 
                             min_value=0.1, value=0.5, step=0.1)
        
        st.subheader("Stage 1: Before Concrete Placement")
        Q_w1 = st.number_input("Workers & equipment (kPa) - Stage 1", 
                              min_value=0.5, value=1.0, step=0.1)
        Q_m1 = st.number_input("Material storage (kPa) - Stage 1", 
                              min_value=0.0, value=0.0, step=0.1)
        
        st.subheader("Stage 2: During Concrete Placement")
        Q_w2 = st.number_input("Workers & equipment (kPa) - Stage 2", 
                              min_value=0.5, value=2.0, step=0.1)
        Q_m2 = st.number_input("Material storage (kPa) - Stage 2", 
                              min_value=0.0, value=2.5, step=0.1)
        
        st.subheader("Stage 3: After Concrete Placement")
        Q_w3 = st.number_input("Workers & equipment (kPa) - Stage 3", 
                              min_value=0.5, value=1.0, step=0.1)
        Q_m3 = st.number_input("Material storage (kPa) - Stage 3", 
                              min_value=0.0, value=0.0, step=0.1)
    
    # Calculate loads
    G_c = calculate_concrete_load(thickness, reinforcement)
    
    # Compute combinations
    results = {
        "1": {"desc": "Prior to concrete", "Q_w": Q_w1, "Q_m": Q_m1, "combs": compute_combinations(G_f, G_c, Q_w1, Q_m1, "1")},
        "2": {"desc": "During placement", "Q_w": Q_w2, "Q_m": Q_m2, "combs": compute_combinations(G_f, G_c, Q_w2, Q_m2, "2")},
        "3": {"desc": "After placement", "Q_w": Q_w3, "Q_m": Q_m3, "combs": compute_combinations(G_f, G_c, Q_w3, Q_m3, "3")}
    }
    
    # Find maximum load
    max_load = max(max(stage["combs"]) for stage in results.values())
    critical_stage = next(k for k,v in results.items() if max(v["combs"]) == max_load)
    
    # Store results in session state
    st.session_state.design_load = max_load
    st.session_state.concrete_thickness = thickness
    
    # Display results
    st.subheader("Results Summary")
    cols = st.columns(3)
    cols[0].metric("Concrete Load (G_c)", f"{G_c:.2f} kPa")
    cols[1].metric("Max Design Load", f"{max_load:.2f} kPa")
    cols[2].metric("Critical Stage", f"Stage {critical_stage}")
    
    st.subheader("Detailed Combinations")
    for stage, data in results.items():
        with st.expander(f"Stage {stage}: {data['desc']}"):
            df = pd.DataFrame({
                "Case": [f"Comb {i+1}" for i in range(2)],
                "Load (kPa)": data["combs"],
                "Formula": [
                    "1.35 × G_f" if stage == "1" and i == 0 
                    else f"1.3 × ({'1.2' if i==1 else '1.35'} × G_f + {f'1.2 × G_c + ' if stage!='1' else ''}1.5 × Q_w + {'' if stage=='3' and i==0 else '1.5 × Q_m'})"
                    for i in range(2)
                ]
            })
            st.dataframe(df.style.format({"Load (kPa)": "{:.2f}"}), hide_index=True)

# ========================
# FORMWORK DESIGNER MODULE
# ========================
def design_formwork(system, span, width, design_load, concrete_thickness, support_type=None):
    """Design formwork system with validation checks"""
    specs = {
        FormworkSystem.PERI_SKYDECK: {
            "max_span": 4.5,
            "min_span": 1.0,
            "capacity": {
                SkydeckSupportType.NO_SUPPORT: 15.0,
                SkydeckSupportType.BEAM_SUPPORT: 18.0,
                SkydeckSupportType.PANEL_SUPPORT: 22.0,
                SkydeckSupportType.BOTH_SUPPORT: 25.0
            },
            "max_concrete": {
                SkydeckSupportType.NO_SUPPORT: 0.43,
                SkydeckSupportType.BEAM_SUPPORT: 0.52,
                SkydeckSupportType.PANEL_SUPPORT: 0.90,
                SkydeckSupportType.BOTH_SUPPORT: 1.09
            },
            "spacings": [0.9, 1.2, 1.5]
        },
        FormworkSystem.GRIDFLEX: {
            "max_span": 3.6,
            "min_span": 0.6,
            "capacity": 12.0,
            "max_concrete": 0.35,
            "spacings": [0.6, 0.9, 1.2]
        },
        FormworkSystem.ALPHADECK: {
            "max_span": 5.0,
            "min_span": 1.2,
            "capacity": 18.0,
            "max_concrete": 0.60,
            "spacings": [1.0, 1.2, 1.5, 1.8]
        }
    }
    
    spec = specs[system]
    
    # Get capacity based on system
    if system == FormworkSystem.PERI_SKYDECK:
        capacity = spec["capacity"][support_type]
        max_concrete = spec["max_concrete"][support_type]
    else:
        capacity = spec["capacity"]
        max_concrete = spec["max_concrete"]
    
    # Validate inputs
    if not (spec["min_span"] <= span <= spec["max_span"]):
        return {"error": f"Span must be between {spec['min_span']}m and {spec['max_span']}m"}
    if concrete_thickness > max_concrete:
        return {"error": f"Concrete thickness exceeds maximum {max_concrete*1000:.0f}mm for this configuration"}
    if design_load > capacity:
        return {"error": f"Design load exceeds system capacity of {capacity} kPa"}
    
    # Determine joist spacing
    spacing = next((s for s in sorted(spec["spacings"], reverse=True 
                   if design_load <= capacity * 0.9), None)
    if not spacing:
        return {"error": "No standard spacing can support the applied loads"}
    
    num_joists = int(width // spacing) + 1
    actual_spacing = width / (num_joists - 1)
    
    return {
        "system": system.value,
        "span": span,
        "width": width,
        "joist_spacing": actual_spacing,
        "num_joists": num_joists,
        "capacity": capacity,
        "max_concrete": max_concrete,
        "support_type": support_type.value if support_type else None
    }

def formwork_designer_module():
    st.header("Formwork System Designer")
    
    # System selection
    system = st.selectbox(
        "Formwork System",
        options=[s.value for s in FormworkSystem],
        key="formwork_system"
    )
    system_enum = next(s for s in FormworkSystem if s.value == system)
    
    # Skydeck support options
    support_type = None
    if system_enum == FormworkSystem.PERI_SKYDECK:
        support_type = st.selectbox(
            "PERI Skydeck Support Type",
            options=[s.value for s in SkydeckSupportType],
            key="skydeck_support"
        )
        support_type = next(s for s in SkydeckSupportType if s.value == support_type)
    
    # Design parameters
    col1, col2 = st.columns(2)
    with col1:
        span = st.number_input("Span (m)", min_value=0.5, max_value=10.0, value=3.0, step=0.1)
        design_load = st.number_input(
            "Design Load (kPa)", 
            min_value=1.0, 
            value=st.session_state.get("design_load", 10.0), 
            step=0.1
        )
    with col2:
        width = st.number_input("Width (m)", min_value=0.5, max_value=20.0, value=5.0, step=0.1)
        concrete_thickness = st.number_input(
            "Concrete Thickness (m)", 
            min_value=0.1, 
            max_value=1.5, 
            value=st.session_state.get("concrete_thickness", 0.2), 
            step=0.05
        )
    
    if st.button("Design Formwork"):
        result = design_formwork(
            system_enum, span, width, 
            design_load, concrete_thickness, 
            support_type
        )
        
        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Design successful!")
            
            # Display results
            st.subheader("Design Summary")
            cols = st.columns(4)
            cols[0].metric("System", result["system"])
            cols[1].metric("Span", f"{result['span']} m")
            cols[2].metric("Width", f"{result['width']} m")
            cols[3].metric("Design Load", f"{design_load:.2f} kPa")
            
            if result["support_type"]:
                st.metric("Support Type", result["support_type"])
            
            st.subheader("Design Specifications")
            spec_cols = st.columns(3)
            spec_cols[0].metric("Joist Spacing", f"{result['joist_spacing']:.2f} m")
            spec_cols[1].metric("Number of Joists", result["num_joists"])
            spec_cols[2].metric("Safety Factor", "1.3")
            
            st.subheader("System Limits")
            limit_cols = st.columns(2)
            limit_cols[0].metric("Max Concrete Thickness", f"{result['max_concrete']*1000:.0f} mm")
            limit_cols[1].metric("System Capacity", f"{result['capacity']:.2f} kPa")

# ========================
# MAIN APP
# ========================
def main():
    st.set_page_config(page_title="Formwork Design Suite", layout="wide")
    st.title("Integrated Formwork Design Suite")
    
    tab1, tab2 = st.tabs(["Load Calculator", "Formwork Designer"])
    
    with tab1:
        load_calculator_module()
    
    with tab2:
        formwork_designer_module()

if __name__ == "__main__":
    main()
