import streamlit as st
import pandas as pd

# -----------------------------
# Module 1: Load Calculator
# -----------------------------
def calculate_concrete_load(thickness, reinforcement_percentage):
    base_density = 24.50  # kN/m³
    reinforcement_load = 0.5 * reinforcement_percentage  # kN/m²
    return base_density * thickness + reinforcement_load * thickness

def compute_combinations(G_f, G_c, Q_w, Q_m, stage):
    gamma_d = 1.3
    if stage == "1":
        return [
            1.35 * G_f,
            gamma_d * (1.2 * G_f + 1.5 * Q_w + 1.5 * Q_m)
        ]
    elif stage in ["2", "3"]:
        return [
            gamma_d * (1.35 * G_f + 1.35 * G_c),
            gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m)
        ]

def module_1():
    st.subheader("🧮 Load Calculator (AS 3610.2)")
    
    with st.sidebar:
        st.subheader("Project Details")
        st.text_input("Project Name", key="project_name", placeholder="e.g. Sydney Metro Stage 2")
        st.text_input("Project Number", key="project_number", placeholder="e.g. P-24123")
        st.text_input("Section/Zone", key="section_detail", placeholder="e.g. Tunnel Shaft A")
        
        st.subheader("Material Properties")
        thickness = st.number_input("Concrete thickness (m)", 0.05, 1.5, 0.2, 0.05)
        reinforcement = st.number_input("Reinforcement percentage (%)", 0.0, 5.0, 1.0, 0.5)
        G_f = st.number_input("Formwork self-weight (kPa)", 0.1, value=0.5, step=0.1)
        
        st.subheader("Stage 1: Before Concrete Placement")
        Q_w1 = st.number_input("Workers & equipment (kPa) - Stage 1", 0.5, value=1.0, step=0.1)
        Q_m1 = st.number_input("Material storage (kPa) - Stage 1", 0.0, value=0.0, step=0.1)
        
        st.subheader("Stage 2: During Concrete Placement")
        Q_w2 = st.number_input("Workers & equipment (kPa) - Stage 2", 0.5, value=2.0, step=0.1)
        Q_m2 = st.number_input("Material storage (kPa) - Stage 2", 0.0, value=2.5, step=0.1)
        
        st.subheader("Stage 3: After Concrete Placement")
        Q_w3 = st.number_input("Workers & equipment (kPa) - Stage 3", 0.5, value=1.0, step=0.1)
        Q_m3 = st.number_input("Material storage (kPa) - Stage 3", 0.0, value=0.0, step=0.1)

    G_c = calculate_concrete_load(thickness, reinforcement)
    results = {
        "1": {"desc": "Prior to concrete", "Q_w": Q_w1, "Q_m": Q_m1,
              "combs": compute_combinations(G_f, G_c, Q_w1, Q_m1, "1")},
        "2": {"desc": "During placement", "Q_w": Q_w2, "Q_m": Q_m2,
              "combs": compute_combinations(G_f, G_c, Q_w2, Q_m2, "2")},
        "3": {"desc": "After placement", "Q_w": Q_w3, "Q_m": Q_m3,
              "combs": compute_combinations(G_f, G_c, Q_w3, Q_m3, "3")}
    }

    max_load = max(max(stage["combs"]) for stage in results.values())
    critical_stage = next(k for k,v in results.items() if max(v["combs"]) == max_load)

    st.session_state.design_load = max_load
    st.session_state.concrete_thickness = thickness

    st.markdown(f"### 📌 Project: {st.session_state.get('project_name', '-')}")
    st.markdown(f"**Project Number:** {st.session_state.get('project_number', '-')}")
    st.markdown(f"**Section/Zone:** {st.session_state.get('section_detail', '-')}")

    cols = st.columns(3)
    cols[0].metric("Concrete Load (G_c)", f"{G_c:.2f} kPa")
    cols[1].metric("Max Design Load", f"{max_load:.2f} kPa")
    cols[2].metric("Critical Stage", f"Stage {critical_stage}")

    st.subheader("Detailed Load Combinations")
    for stage, data in results.items():
        with st.expander(f"Stage {stage}: {data['desc']}"):
            df = pd.DataFrame({
                "Case": [f"Comb {i+1}" for i in range(2)],
                "Load (kPa)": data["combs"],
                "Formula": [
                    "1.35 × G_f" if stage == "1" and i == 0 
                    else f"1.3 × ({'1.2' if i==1 else '1.35'} × G_f"
                         f"{' + 1.2 × G_c' if stage != '1' else ''} + 1.5 × Q_w + 1.5 × Q_m)"
                    for i in range(2)
                ]
            })
            st.dataframe(df.style.format({"Load (kPa)": "{:.2f}"}), hide_index=True)

# -----------------------------
# Module 2: Design Checker
# -----------------------------
def module_2():
    st.subheader("🛠️ Formwork Design – System Selection")

    system = st.selectbox("Select Formwork System", ["PERI Skydeck", "PERI GRIDFLEX", "PERI ALPHADECK"])

    thickness = st.session_state.get("concrete_thickness", None)

    if system == "PERI Skydeck":
        st.subheader("Skydeck Configuration")
        support_option = st.selectbox(
            "Select Mid-Support Option",
            [
                "No mid-support used",
                "Mid support under beam",
                "Mid support under panel",
                "Mid support under both panel and beam"
            ]
        )

        support_limits = {
            "No mid-support used": 0.430,
            "Mid support under beam": 0.520,
            "Mid support under panel": 0.900,
            "Mid support under both panel and beam": 1.090,
        }

        if thickness is not None:
            limit = support_limits[support_option]
            is_safe = thickness <= limit

            st.markdown(f"**Concrete Thickness:** {thickness:.3f} m")
            st.markdown(f"**Skydeck Limit:** {limit:.3f} m")

            if is_safe:
                st.success("✅ This configuration is suitable for the applied concrete thickness.")
            else:
                st.error("❌ This configuration is NOT suitable for the applied concrete thickness.")
        else:
            st.warning("⚠️ Concrete thickness not available. Please run Module 1 first.")

# -----------------------------
# App Main Function
# -----------------------------
def main():
    st.set_page_config(page_title="Formwork App", layout="wide")
    st.title("🧱 Formwork Load & Design Tool")

    # Radio buttons to select module
    module = st.radio("Select Module", ("Load Calculator", "Design Module"))

    if module == "Load Calculator":
        module_1()
    elif module == "Design Module":
        module_2()

if __name__ == "__main__":
    main()
