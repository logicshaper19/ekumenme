#!/usr/bin/env python3
"""
Demo script showing how AI Quality Assessment works
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.knowledge_base_workflow import KnowledgeBaseWorkflowService, DocumentType

async def demo_quality_assessment():
    print('🔍 AI Quality Assessment Demo')
    print('=' * 50)
    
    # Create test content
    test_content = '''
Agricultural Best Practices Guide

Wheat Cultivation:
- Plant wheat in autumn for optimal growth
- Use certified seeds for better yield
- Apply nitrogen fertilizer at recommended rates
- Monitor for diseases like rust and fusarium
- Harvest when moisture content is below 14%

Soil Management:
- Test soil pH annually
- Maintain organic matter above 2%
- Use cover crops to prevent erosion
- Rotate crops to break disease cycles

This guide provides evidence-based recommendations for sustainable agriculture.
    '''
    
    # Save to file
    test_file = '/tmp/demo_document.txt'
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        # Initialize service
        workflow_service = KnowledgeBaseWorkflowService()
        
        # Run assessment
        print('🤖 Running AI quality assessment...')
        assessment = await workflow_service._assess_content_quality(test_file, DocumentType.MANUAL)
        
        print(f'\n📊 Quality Assessment Results:')
        print(f'   Overall Score: {assessment.score}/100')
        print(f'   Acceptable (≥70): {assessment.is_acceptable()}')
        print(f'   Issues Found: {len(assessment.issues)}')
        print(f'   Recommendations: {len(assessment.recommendations)}')
        print()
        
        if assessment.issues:
            print('⚠️  Issues Identified:')
            for i, issue in enumerate(assessment.issues, 1):
                print(f'   {i}. {issue}')
            print()
        
        if assessment.recommendations:
            print('💡 Recommendations:')
            for i, rec in enumerate(assessment.recommendations, 1):
                print(f'   {i}. {rec}')
            print()
        
        # Show workflow decision
        print('🔄 Workflow Decision:')
        if assessment.is_acceptable():
            print('   ✅ Document meets quality threshold - can be auto-approved')
            print('   📝 Status: under_review → approved (auto)')
        else:
            print('   ⚠️  Document needs manual review')
            print('   📝 Status: under_review → awaiting superadmin approval')
        
        print('\n✅ Assessment completed!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(demo_quality_assessment())
