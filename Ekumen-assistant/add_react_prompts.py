#!/usr/bin/env python3
"""
Add get_X_react_prompt functions to remaining prompt files.
"""

import re

def add_react_prompt_to_file(agent_name, agent_title, tools_desc, example_1, example_2):
    """Add get_X_react_prompt function to a prompt file"""
    
    filename = f'app/prompts/{agent_name}_prompts.py'
    
    # Read the file
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find the __all__ section
    all_match = re.search(r'__all__ = \[(.*?)\]', content, re.DOTALL)
    if not all_match:
        print(f"ERROR: Could not find __all__ in {filename}")
        return False
    
    # Create the new function
    function_code = f'''
# ReAct-compatible prompt template for {agent_title} Agent
def get_{agent_name}_react_prompt(include_examples: bool = False) -> ChatPromptTemplate:
    """
    Get ReAct-compatible ChatPromptTemplate for {agent_title} Intelligence Agent.
    
    This combines the sophisticated {agent_name.replace('_', ' ')} expertise with ReAct format
    for tool-using agents.
    
    Args:
        include_examples: Whether to include few-shot examples (default False for token optimization)
        
    Returns:
        ChatPromptTemplate configured for ReAct agent with {agent_name.replace('_', ' ')} expertise
    """
    
    # Build examples section if requested
    examples_section = ""
    if include_examples:
        examples_section = """

EXEMPLES DE RAISONNEMENT RÉUSSI:

{example_1}

{example_2}"""
    
    # Enhanced system prompt with ReAct format
    react_system_prompt = f"""{{{agent_name.upper()}_SYSTEM_PROMPT}}

Tu as accès à ces outils pour obtenir des données précises:
{{{{tools}}}}

Noms des outils disponibles: {{{{tool_names}}}}

UTILISATION DES OUTILS:
{tools_desc}

FORMAT REACT OBLIGATOIRE:
Tu dois suivre ce format de raisonnement:

Question: la question de l'utilisateur
Thought: [analyse de ce que tu dois faire et quel outil utiliser]
Action: [nom exact de l'outil à utiliser]
Action Input: [paramètres de l'outil au format JSON]
Observation: [résultat retourné par l'outil]
... (répète Thought/Action/Action Input/Observation autant de fois que nécessaire)
Thought: je connais maintenant la réponse finale avec toutes les données nécessaires
Final Answer: [réponse complète en français avec toutes les analyses]
{{examples_section}}

IMPORTANT:
- Utilise TOUJOURS les outils pour obtenir des données précises
- Ne devine JAMAIS les informations
- Fournis des analyses précises avec chiffres et recommandations
- Suis EXACTEMENT le format ReAct ci-dessus"""

    # Create ChatPromptTemplate with ReAct format
    return ChatPromptTemplate.from_messages([
        ("system", react_system_prompt),
        ("human", """{{{{context}}}}

Question: {{{{input}}}}"""),
        ("ai", "{{agent_scratchpad}}")
    ])


'''
    
    # Insert before __all__
    all_start = all_match.start()
    new_content = content[:all_start] + function_code + content[all_start:]
    
    # Add to __all__
    new_content = new_content.replace(
        all_match.group(0),
        all_match.group(0).replace(']', f',\n    "get_{agent_name}_react_prompt"\n]')
    )
    
    # Write back
    with open(filename, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Added get_{agent_name}_react_prompt to {filename}")
    return True


# Planning Agent
add_react_prompt_to_file(
    'planning',
    'Planning',
    '''Utilise TOUJOURS les outils pour obtenir des données précises plutôt que de deviner.
- Pour créer un plan: utilise create_intervention_plan
- Pour optimiser les rotations: utilise optimize_crop_rotation
- Pour planifier les semis: utilise plan_sowing_schedule
- Pour calculer les besoins: utilise calculate_resource_needs''',
    '''Exemple 1 - Planification d'intervention:
Question: Crée un plan d'intervention pour ma parcelle de blé
Thought: Je dois créer un plan d'intervention complet
Action: create_intervention_plan
Action Input: {{"crop": "blé", "parcel_id": "BLE-001", "season": "2024"}}
Observation: Plan créé - 5 interventions planifiées (semis, fertilisation, traitements)
Thought: J'ai le plan, je peux le présenter
Final Answer: **Plan d'Intervention Blé 2024:**
- Semis: Octobre 2023
- Fertilisation: Mars 2024
- Traitements: Avril-Mai 2024''',
    '''Exemple 2 - Rotation des cultures:
Question: Optimise ma rotation sur 3 ans
Thought: Je dois optimiser la rotation
Action: optimize_crop_rotation
Action Input: {{"years": 3, "current_crop": "blé"}}
Observation: Rotation optimisée - Blé → Colza → Orge
Final Answer: **Rotation Optimisée:**
Année 1: Blé
Année 2: Colza
Année 3: Orge'''
)

# Regulatory Agent
add_react_prompt_to_file(
    'regulatory',
    'Regulatory',
    '''Utilise TOUJOURS les outils pour vérifier la conformité réglementaire.
- Pour vérifier un produit: utilise check_product_authorization
- Pour les délais: utilise check_reentry_period
- Pour les doses: utilise validate_application_rate
- Pour les restrictions: utilise check_usage_restrictions''',
    '''Exemple 1 - Vérification produit:
Question: Puis-je utiliser ce produit sur mon blé?
Thought: Je dois vérifier l'autorisation du produit
Action: check_product_authorization
Action Input: {{"product_amm": "2020001", "crop": "blé"}}
Observation: Produit autorisé - Usage autorisé sur blé, dose max 1.5L/ha
Thought: Le produit est autorisé, je peux confirmer
Final Answer: ✅ Produit autorisé sur blé
Dose maximale: 1.5L/ha''',
    '''Exemple 2 - Délai de rentrée:
Question: Quel est le délai de rentrée?
Thought: Je dois vérifier le délai réglementaire
Action: check_reentry_period
Action Input: {{"product_amm": "2020001"}}
Observation: Délai de rentrée: 48 heures
Final Answer: Délai de rentrée: 48 heures'''
)

# Sustainability Agent
add_react_prompt_to_file(
    'sustainability',
    'Sustainability',
    '''Utilise TOUJOURS les outils pour évaluer la durabilité.
- Pour l'empreinte carbone: utilise calculate_carbon_footprint
- Pour la biodiversité: utilise assess_biodiversity_impact
- Pour l'eau: utilise evaluate_water_usage
- Pour le sol: utilise analyze_soil_health''',
    '''Exemple 1 - Empreinte carbone:
Question: Calcule l'empreinte carbone de mon exploitation
Thought: Je dois calculer l'empreinte carbone
Action: calculate_carbon_footprint
Action Input: {{"farm_id": "FARM123", "year": 2023}}
Observation: Empreinte: 450 tCO2eq/an, moyenne: 500 tCO2eq/an
Thought: L'empreinte est calculée, je peux analyser
Final Answer: **Empreinte Carbone 2023:**
Total: 450 tCO2eq/an
✅ 10% en dessous de la moyenne''',
    '''Exemple 2 - Biodiversité:
Question: Évalue l'impact sur la biodiversité
Thought: Je dois évaluer l'impact biodiversité
Action: assess_biodiversity_impact
Action Input: {{"farm_id": "FARM123"}}
Observation: Score biodiversité: 7/10 - Bon niveau
Final Answer: Score biodiversité: 7/10 ✅'''
)

print("\n✅ All ReAct prompts added successfully!")

