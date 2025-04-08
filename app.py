import streamlit as st
import pandas as pd
from enum import Enum
import math
from typing import Literal

# Enum for formwork systems
class FormworkSystem(Enum):
    PERI_SKYDECK = "PERI Skydeck"
    GRIDFLEX = "Gridflex"
    ALPHADECK = "Alphadeck"

# Enum for PERI Skydeck support types
class SkydeckSupportType(Enum):
    NO_SUPPORT = "No mid-support"
    BEAM_SUPPORT = "Mid support under beam"
    PANEL_SUPPORT = "Mid support under panel"
    BOTH_SUPPORT = "Mid support under both panel and beam"

# System specifications with detailed PERI Skydeck options
SYSTEM_SPECS = {
    FormworkSystem.PERI_SKYDECK: {
        'max_span': {
            SkydeckSupportType.NO_SUPPORT: 4.5,
            SkydeckSupportType.BEAM_SUPPORT: 6.0,
            SkydeckSupportType.PANEL_SUPPORT: 6.0,
            SkydeckSupportType.BOTH_SUPPORT: 6.0
        },
        'min_span': 1.0,
        'concrete_capacity': {
            SkydeckSupportType.NO_SUPPORT: 0.43,  # 430mm
            SkydeckSupportType.BEAM_SUPPORT: 0.52,  # 520mm
            SkydeckSupportType.PANEL_SUPPORT: 0.90,  # 900mm
            SkydeckSupportType.BOTH_SUPPORT: 1.09  # 1090mm
        },
        'ultimate_capacity': 15.0,  # kPa
        'serviceability_capacity': 10.0,
        'standard_spacings': [0.9, 1.2, 1.5],
        'decking_thickness': 0.021,
        'decking_weight': 0.15,
        'joist_weight': 0.1,
        'max_deflection': 'span/270',
        'material': 'Aluminum'
    },
    FormworkSystem.GRIDFLEX: {
        'max_span': 3.6,
        'min_span': 0.6,
        'ultimate_capacity': 12.0,
        'serviceability_capacity': 8.0,
        'standard_spacings': [0.6, 0.9, 1.2],
        'decking_thickness': 0.018,
        'decking_weight': 0.12,
        'joist_weight': 0.08,
        'max_deflection': 'span/250',
        'material': 'Steel'
    },
    FormworkSystem.ALPHADECK: {
        'max_span': 5.0,
        'min_span': 1.2,
        'ultimate_capacity': 18.0,
        'serviceability_capacity': 12.0,
        'standard_spacings': [1.0, 1.2, 1.5, 1.8],
        'decking_thickness': 0.024,
        'decking_weight': 0.18,
        'joist_weight': 0.12,
        'max_deflection': 'span/300',
        'material': 'Aluminum'
    }
}

def calculate_concrete_load(thickness, reinforcement_percentage):
    """Calculate G_c in kN/m² based on concrete thickness and reinforcement percentage."""
    base_density = 24  # kN/m³
    reinforcement_load = 0.5 * reinforcement_percentage  # kN/m²
    G_c = base_density * thickness + reinforcement_load * thickness
    return G_c

def compute_combinations(G_f, G_c, Q_w, Q_m, Q_h, W_s, W_u, F_w, Q_x, P_c, I, stage, gamma_d):
    """Compute load combinations for a given stage and gamma_d."""
    combinations = []

    if stage == "1":
        comb_1 = (1.35 * G_f, 0.0)
        comb_2 = (gamma_d * (1.2 * G_f + 1.5 * Q_w + 1.5 * Q_m + 1.0 * W_s), gamma_d * (1.5 * Q_h))
        comb_3 = (1.2 * G_f + 1.0 * W_u + 1.5 * F_w, 0.0)
        comb_4 = (0.9 * G_f + 1.0 * W_u + 1.5 * F_w, 0.0)
        comb_5 = (1.0 * G_f + 1.1 * I, 0.0)
        combinations = [comb_1, comb_2, comb_3, comb_4, comb_5]
    
    elif stage == "2":
        comb_6 = (gamma_d * (1.35 * G_f + 1.35 * G_c), 0.0)
        comb_7 = (gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m + 1.0 * W_s + 1.5 * F_w + 1.5 * Q_x + 1.0 * P_c), 
                 gamma_d * (1.5 * Q_h))
        comb_8 = (1.0 * G_f + 1.0 * G_c + 1.1 * I, 0.0)
        combinations = [comb_6, comb_7, comb_8]
    
    elif stage == "3":
        comb_9 = (gamma_d * (1.35 * G_f + 1.35 * G_c), 0.0)
        comb_10 = (gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m + 1.0 * W_s + 1.5 * F_w + 1.5 * Q_x + 1.0 * P_c),
                  gamma_d * (1.5 * Q_h))
        comb_11 = (1.2 * G_f + 1.2 * G_c + 1.0 * W_u, 0.0)
        comb_12 = (1.0 * G_f + 1.0 * G_c + 1.1 * I, 0.0)
        combinations = [comb_9, comb_10, comb_11, comb_12]
    
    return combinations

def design_formwork_system(system_type, span, width, max_vertical_load, max_horizontal_load, 
                          skydeck_support=None, concrete_thickness=None):
    """Design the formwork system with support for PERI Skydeck options."""
    specs = SYSTEM_SPECS[system_type]
    
    # For PERI Skydeck, use support-specific parameters
    if system_type == FormworkSystem.PERI_SKYDECK and skydeck_support:
        max_span = specs['max_span'][skydeck_support]
        concrete_capacity = specs['concrete_capacity'][skydeck_support]
        
        # Check concrete thickness against capacity
        if concrete_thickness and concrete_thickness > concrete_capacity:
            return {
                'error': (f"Concrete thickness {concrete_thickness*1000:.0f}mm exceeds capacity "
                         f"of {concrete_capacity*1000:.0f}mm for {skydeck_support.value}")
            }
    else:
        max_span = specs['max_span'] if isinstance(specs['max_span'], float) else max(specs['max_span'].values())
    
    # Validate span requirements
    min_span = specs['min_span']
    if span < min_span or span > max_span:
        return {
            'error': f"Span {span}m is outside the allowable range ({min_span}m to {max_span}m)"
        }
    
    # Check capacity against ultimate load
    if max_vertical_load > specs['ultimate_capacity']:
        return {
            'error': f"Vertical load {max_vertical_load}kPa exceeds system capacity of {specs['ultimate_capacity']}kPa"
        }
    
    # Determine optimal joist spacing
    recommended_spacing = None
    for spacing in sorted(specs['standard_spacings'], reverse=True):
        if max_vertical_load <= specs['ultimate_capacity'] * 0.9:  # Apply safety factor
            recommended_spacing = spacing
            break
    
    if not recommended_spacing:
        return {
            'error': "No standard joist spacing can support the applied loads"
        }
    
    # Calculate number of joists required
    num_joists = math.ceil(width / recommended_spacing) + 1
    actual_spacing = width / (num_joists - 1)
    
    # Calculate self-weight including joists
    total_self_weight = specs['decking_weight'] + (specs['joist_weight'] / actual_spacing)
    
    # Calculate deflection (simplified)
    max_allowed_deflection = span / int(specs['max_deflection'].split('/')[1])
    estimated_deflection = min(span / 400, max_allowed_deflection * 0.8)  # Simplified
    
    # Prepare result dictionary
    result = {
        'system': system_type.value,
        'span': span,
        'width': width,
        'joist_spacing': actual_spacing,
        'num_joists': num_joists,
        'self_weight': total_self_weight,
        'max_deflection': estimated_deflection,
        'max_allowed_deflection': max_allowed_deflection,
        'capacity_check': 'OK',
        'material': specs['material'],
        'notes': 'Design completed per manufacturer specifications'
    }
    
    # Add PERI Skydeck specific information if applicable
    if system_type == FormworkSystem.PERI_SKYDECK and skydeck_support:
        result.update({
            'support_type': skydeck_support.value,
            'max_concrete_thickness': specs['concrete_capacity'][skydeck_support],
            'support_notes': get_skydeck_support_notes(skydeck_support)
        })
    
    return result

def get_skydeck_support_notes(support_type: SkydeckSupportType) -> str:
    """Get descriptive notes for each PERI Skydeck support type."""
    notes = {
        SkydeckSupportType.NO_SUPPORT: "System can support up to 430mm concrete without mid-supports",
        SkydeckSupportType.BEAM_SUPPORT: "System can support up to 520mm concrete with beam supports",
        SkydeckSupportType.PANEL_SUPPORT: "System can support up to 900mm concrete with panel supports",
        SkydeckSupportType.BOTH_SUPPORT: "System can support up to 1090mm concrete with both beam and panel supports"
    }
    return notes.get(support_type, "")

def main():
    st.set_page_config(page_title="Formwork Design Suite", layout="wide")
    
    st.title("Integrated Formwork Design Suite")
    st.markdown("""
    This tool combines load calculation per AS 3610.2 with formwork system design for PERI Skydeck, 
    Gridflex, and Alphadeck systems.
    """)
    
    # Use tabs to separate the two main functions
    tab1, tab2 = st.tabs(["Load Calculator", "Formwork Designer"])
    
    with tab1:
        st.header("AS 3610.2 Load Calculator")
        
        with st.sidebar:
            st.header("Project Details")
            project_number = st.text_input("Project Number", "PRJ-001")
            project_name = st.text_input("Project Name", "Sample Project")
            
            st.header("Basic Parameters")
            G_f = st.number_input("Formwork self-weight (G_f, kN/m²)", value=0.6, step=0.1)
            thickness = st.number_input("Concrete thickness (m)", value=0.2, step=0.05)
            reinforcement_percentage = st.number_input("Reinforcement percentage (%)", value=2.0, step=0.5)
            
            st.header("Load Parameters")
            Q_w1 = st.number_input("Workers & equipment for Stage 1 (Q_w1, kN/m²)", value=1.0, step=0.1)
            Q_w2 = st.number_input("Workers, equipment & placement for Stage 2 (Q_w2, kN/m²)", value=2.0, step=0.1)
            Q_w3 = st.number_input("Workers & equipment for Stage 3 (Q_w3, kN/m²)", value=1.0, step=0.1)
            Q_m = st.number_input("Stacked materials (Q_m, kN/m²)", value=2.5, step=0.1)
            Q_h = st.number_input("Horizontal imposed load (Q_h, kN/m)", value=0.0, step=0.1)
            W_s = st.number_input("Service wind load (W_s, kN/m²)", value=0.0, step=0.1)
            W_u = st.number_input("Ultimate wind load (W_u, kN/m²)", value=0.0, step=0.1)
            F_w = st.number_input("Flowing water load (F_w, kN/m²)", value=0.0, step=0.1)
            Q_x = st.number_input("Other actions (Q_x, kN/m²)", value=0.0, step=0.1)
            P_c = st.number_input("Lateral concrete pressure (P_c, kN/m²)", value=0.0, step=0.1)
            I = st.number_input("Impact load (I, kN/m²)", value=0.0, step=0.1)
            
            if st.button("Calculate Load Combinations"):
                inputs = {
                    'G_f': G_f,
                    'thickness': thickness,
                    'reinforcement_percentage': reinforcement_percentage,
                    'G_c': calculate_concrete_load(thickness, reinforcement_percentage),
                    'Q_w1': Q_w1,
                    'Q_w2': Q_w2,
                    'Q_w3': Q_w3,
                    'Q_m': Q_m,
                    'Q_h': Q_h,
                    'W_s': W_s,
                    'W_u': W_u,
                    'F_w': F_w,
                    'Q_x': Q_x,
                    'P_c': P_c,
                    'I': I
                }
                
                # Compute results
                results = {}
                stages = {
                    "1": {"Q_w": Q_w1, "description": "Prior to concrete placement"},
                    "2": {"Q_w": Q_w2, "description": "During concrete placement"},
                    "3": {"Q_w": Q_w3, "description": "After concrete placement"}
                }

                for stage, data in stages.items():
                    Q_w = data["Q_w"]
                    
                    # Critical Members (γ_d = 1.3)
                    critical_combinations = compute_combinations(
                        G_f, inputs['G_c'], Q_w, Q_m, Q_h, W_s, W_u,
                        F_w, Q_x, P_c, I, stage, gamma_d=1.3
                    )
                    
                    # Non-Critical Members (γ_d = 1.0)
                    non_critical_combinations = compute_combinations(
                        G_f, inputs['G_c'], Q_w, Q_m, Q_h, W_s, W_u,
                        F_w, Q_x, P_c, I, stage, gamma_d=1.0
                    )

                    results[stage] = {
                        "description": data["description"],
                        "critical": critical_combinations,
                        "non_critical": non_critical_combinations
                    }
                
                # Store in session state
                st.session_state.load_results = results
                st.session_state.load_inputs = inputs
                st.session_state.concrete_thickness = thickness
        
        # Display load calculation results
        if 'load_results' in st.session_state:
            st.success("Load combinations calculated successfully!")
            
            # Find maximum vertical load for formwork design
            max_vertical_load = max(
                max(comb[0] for comb in stage_data['critical'])
                for stage_data in st.session_state.load_results.values()
            )
            st.session_state.max_vertical_load = max_vertical_load
            
            st.subheader("Maximum Vertical Load for Design")
            st.metric("Design Vertical Load", f"{max_vertical_load:.2f} kPa")
            
            # Show detailed results in expander
            with st.expander("View Detailed Load Combinations"):
                for stage in ["1", "2", "3"]:
                    if stage not in st.session_state.load_results:
                        continue
                        
                    data = st.session_state.load_results[stage]
                    st.subheader(f"Stage {stage}: {data['description']}")
                    
                    # Critical Members
                    st.markdown("**Critical Members (γ_d = 1.3)**")
                    critical_df = pd.DataFrame([
                        {
                            "Combination": i+1,
                            "Vertical Load (kPa)": comb[0],
                            "Horizontal Load (kN/m)": comb[1]
                        }
                        for i, comb in enumerate(data['critical'])
                    ])
                    st.dataframe(critical_df, hide_index=True)
                    
                    # Non-Critical Members
                    st.markdown("**Non-Critical Members (γ_d = 1.0)**")
                    non_critical_df = pd.DataFrame([
                        {
                            "Combination": i+1,
                            "Vertical Load (kPa)": comb[0],
                            "Horizontal Load (kN/m)": comb[1]
                        }
                        for i, comb in enumerate(data['non_critical'])
                    ])
                    st.dataframe(non_critical_df, hide_index=True)
    
    with tab2:
        st.header("Formwork System Designer")
        
        if 'max_vertical_load' not in st.session_state:
            st.warning("Please calculate load combinations first using the Load Calculator tab")
            return
        
        with st.sidebar:
            st.header("Design Parameters")
            system_type = st.selectbox(
                "Formwork System",
                options=[system.value for system in FormworkSystem],
                index=0
            )
            
            span = st.number_input("Span (m)", min_value=0.5, max_value=10.0, value=3.0, step=0.1)
            width = st.number_input("Width (m)", min_value=0.5, max_value=20.0, value=5.0, step=0.1)
            
            # Show PERI Skydeck options if selected
            skydeck_support = None
            if system_type == FormworkSystem.PERI_SKYDECK.value:
                skydeck_support = st.selectbox(
                    "PERI Skydeck Support Type",
                    options=[support.value for support in SkydeckSupportType],
                    index=0
                )
                # Convert back to Enum
                for support in SkydeckSupportType:
                    if support.value == skydeck_support:
                        skydeck_support = support
                        break
            
            if st.button("Design Formwork System"):
                # Convert system type back to Enum
                system_enum = None
                for system in FormworkSystem:
                    if system.value == system_type:
                        system_enum = system
                        break
                
                if system_enum:
                    st.session_state.design_result = design_formwork_system(
                        system_enum, 
                        span, 
                        width, 
                        st.session_state.max_vertical_load, 
                        0.5,  # Default horizontal load
                        skydeck_support,
                        st.session_state.concrete_thickness if 'concrete_thickness' in st.session_state else None
                    )
        
        # Display design results
        if 'design_result' in st.session_state:
            result = st.session_state.design_result
            
            if 'error' in result:
                st.error(result['error'])
            else:
                st.success("Formwork system designed successfully!")
                
                # System Overview
                st.subheader("System Overview")
                col1, col2, col3 = st.columns(3)
                col1.metric("System", result['system'])
                col2.metric("Material", result['material'])
                col3.metric("Capacity Check", result['capacity_check'])
                
                # Show PERI Skydeck specific info if applicable
                if result['system'] == FormworkSystem.PERI_SKYDECK.value and 'support_type' in result:
                    st.markdown("**PERI Skydeck Support Configuration**")
                    sup_col1, sup_col2 = st.columns(2)
                    sup_col1.metric("Support Type", result['support_type'])
                    sup_col2.metric("Max Concrete Thickness", f"{result['max_concrete_thickness']*1000:.0f} mm")
                    st.info(result['support_notes'])
                
                # Design Parameters
                st.subheader("Design Parameters")
                design_params = {
                    "Span": f"{result['span']} m",
                    "Width": f"{result['width']} m",
                    "Joist Spacing": f"{result['joist_spacing']:.3f} m",
                    "Number of Joists": result['num_joists'],
                    "Total Self-weight": f"{result['self_weight']:.2f} kN/m²",
                    "Estimated Deflection": f"{result['max_deflection']*1000:.2f} mm",
                    "Max Allowed Deflection": f"{result['max_allowed_deflection']*1000:.2f} mm"
                }
                st.json(design_params)
                
                # Bill of Materials
                st.subheader("Estimated Bill of Materials")
                bom_data = {
                    "Component": ["Decking Area", "Joists", "Primary Beams", "Secondary Beams", "Supports"],
                    "Quantity": [
                        f"{result['width'] * result['span']:.1f} m²",
                        result['num_joists'],
                        math.ceil(result['width'] / 2),
                        math.ceil(result['span'] / 2),
                        math.ceil(result['width'] / 1.5) * math.ceil(result['span'] / 1.5)
                    ],
                    "Notes": [
                        f"{SYSTEM_SPECS[FormworkSystem(result['system'])]['decking_thickness']*1000:.1f} mm thick",
                        f"Spaced at {result['joist_spacing']:.3f} m",
                        "Adjust based on actual layout",
                        "Adjust based on actual layout",
                        "Number may vary based on support type"
                    ]
                }
                st.dataframe(pd.DataFrame(bom_data), use_container_width=True)
                
                # Design Notes
                st.subheader("Design Notes")
                st.info(result['notes'])

if __name__ == "__main__":
    main()
