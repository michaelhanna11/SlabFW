def get_components_description(stage, G_f, G_c, Q_w, Q_m):
    """Return description of load components for each combination."""
    if stage == "1":
        return [
            "1.35 × G_f",  # No γ_d applied
            "1.3 × (1.2 × G_f + 1.5 × Q_w + 1.5 × Q_m)"  # Explicitly show 1.3 factor
        ]
    elif stage == "2":
        return [
            "1.3 × (1.35 × G_f + 1.35 × G_c)",  # Explicitly show 1.3 factor
            "1.3 × (1.2 × G_f + 1.2 × G_c + 1.5 × Q_w + 1.5 × Q_m)"  # Explicitly show 1.3 factor
        ]
    elif stage == "3":
        return [
            "1.3 × (1.35 × G_f + 1.35 × G_c)",  # Explicitly show 1.3 factor
            "1.3 × (1.2 × G_f + 1.2 × G_c + 1.5 × Q_w + 1.5 × Q_m)"  # Explicitly show 1.3 factor
        ]

def compute_combinations(G_f, G_c, Q_w, Q_m, stage):
    """Compute load combinations with unanticipated load factor (γ_d = 1.3)"""
    combinations = []
    gamma_d = 1.3  # Unanticipated load factor
    
    if stage == "1":
        comb_1 = 1.35 * G_f  # No γ_d
        comb_2 = gamma_d * (1.2 * G_f + 1.5 * Q_w + 1.5 * Q_m)
        combinations = [comb_1, comb_2]
    
    elif stage == "2":
        comb_3 = gamma_d * (1.35 * G_f + 1.35 * G_c)
        comb_4 = gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m)
        combinations = [comb_3, comb_4]
    
    elif stage == "3":
        comb_5 = gamma_d * (1.35 * G_f + 1.35 * G_c)
        comb_6 = gamma_d * (1.2 * G_f + 1.2 * G_c + 1.5 * Q_w + 1.5 * Q_m)
        combinations = [comb_5, comb_6]
    
    return combinations
