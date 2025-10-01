#!/usr/bin/env python3
"""
Helper script to replicate the 10/10 production-ready pattern from one agent to another.

Usage:
    python replicate_agent_pattern.py crop_health

This will copy the sophisticated implementation from farm_data_agent to crop_health_agent.
"""

import sys
import re

def replicate_pattern(target_agent):
    """Replicate the pattern from farm_data_agent to target_agent"""
    
    # Read the template (farm_data_agent.py)
    with open('app/agents/farm_data_agent.py', 'r') as f:
        template_content = f.read()
    
    # Read the target agent to preserve the header and tools
    target_file = f'app/agents/{target_agent}_agent.py'
    with open(target_file, 'r') as f:
        target_lines = f.readlines()
    
    # Extract header (first 119 lines which include __init__)
    header = ''.join(target_lines[:119])
    
    # Extract the methods section from template (lines after __init__)
    # Find where _create_agent starts in template
    template_lines = template_content.split('\n')
    create_agent_idx = None
    for i, line in enumerate(template_lines):
        if 'def _create_agent(self):' in line:
            create_agent_idx = i
            break
    
    if create_agent_idx is None:
        print("ERROR: Could not find _create_agent method in template")
        return False
    
    # Get all methods from _create_agent onwards
    methods_section = '\n'.join(template_lines[create_agent_idx:])
    
    # Adapt the methods for the target agent
    adaptations = {
        'farm_data': target_agent.replace('_', ' ').title().replace(' ', ''),
        'Farm Data': target_agent.replace('_', ' ').title(),
        'farm data': target_agent.replace('_', ' '),
        'farm_data_intelligence': f'{target_agent}_intelligence',
        'get_farm_data_react_prompt': f'get_{target_agent}_react_prompt',
        'farm_data_prompts': f'{target_agent}_prompts',
        'MesParcelles", "EPHY", "agri_db': 'diagnostic_tools", "phytosanitary_db',
        'farm_data_retrieval': f'{target_agent}_diagnosis',
        'performance_metrics': 'disease_identification',
        'trend_analysis': 'pest_identification',
        'benchmarking': 'treatment_planning',
        'regulatory_compliance': 'nutrient_analysis'
    }
    
    adapted_methods = methods_section
    for old, new in adaptations.items():
        adapted_methods = adapted_methods.replace(old, new)
    
    # Combine header + adapted methods
    new_content = header + '\n' + adapted_methods
    
    # Write the new file
    with open(target_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Successfully replicated pattern to {target_file}")
    print(f"   - Preserved header and tools")
    print(f"   - Added all sophisticated methods")
    print(f"   - Adapted for {target_agent} agent")
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python replicate_agent_pattern.py <agent_name>")
        print("Example: python replicate_agent_pattern.py crop_health")
        sys.exit(1)
    
    target = sys.argv[1]
    success = replicate_pattern(target)
    sys.exit(0 if success else 1)

