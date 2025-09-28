"""
Crop Health Monitor Agent - Specialized in crop health diagnosis and monitoring.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from .base_agent import IntegratedAgriculturalAgent, AgentState
from ..utils.prompts import FrenchAgriculturalPrompts
from ..data import disease_db, pest_db, deficiency_db
from ..data.french_crop_diseases import GrowthStage, DiseaseSeverity
from ..data.french_crop_pests import PestStage, PestSeverity
from ..data.french_nutrient_deficiencies import DeficiencySeverity
import logging
import re

logger = logging.getLogger(__name__)


class DiseaseDiagnosisTool(BaseTool):
    """Tool for diagnosing crop diseases."""
    
    name: str = "disease_diagnosis"
    description: str = "Diagnostiquer les maladies des cultures à partir des symptômes observés"
    
    def _run(self, crop_type: str, symptoms: str, location: str) -> str:
        """Diagnose crop diseases using the French disease database."""
        try:
            # Parse symptoms from the input string
            symptom_list = self._parse_symptoms(symptoms)
            
            # Find matching diseases
            matching_diseases = disease_db.find_diseases_by_symptoms(crop_type, symptom_list)
            
            if not matching_diseases:
                return f"Aucune maladie identifiée pour {crop_type} avec les symptômes: {symptoms}. Vérifiez la description des symptômes ou consultez un expert."
            
            # Build diagnosis report
            diagnosis_report = f"DIAGNOSTIC POUR {crop_type.upper()} À {location.upper()}\n"
            diagnosis_report += "=" * 50 + "\n\n"
            
            for i, disease in enumerate(matching_diseases[:3], 1):  # Top 3 matches
                diagnosis_report += f"{i}. {disease.name.upper()} ({disease.scientific_name})\n"
                diagnosis_report += f"   Sévérité: {disease.severity.value}\n"
                diagnosis_report += f"   Impact économique: {disease.economic_impact}\n\n"
                
                # Symptoms
                diagnosis_report += "   SYMPTÔMES OBSERVÉS:\n"
                for symptom in disease.symptoms:
                    diagnosis_report += f"   - {symptom.description}\n"
                
                # Treatments
                if disease.treatments:
                    diagnosis_report += "\n   TRAITEMENTS RECOMMANDÉS:\n"
                    for treatment in disease.treatments[:2]:  # Top 2 treatments
                        diagnosis_report += f"   - {treatment.name} ({treatment.active_ingredient})\n"
                        diagnosis_report += f"     Dosage: {treatment.dosage}\n"
                        diagnosis_report += f"     Timing: {treatment.application_timing}\n"
                        diagnosis_report += f"     Efficacité: {treatment.effectiveness*100:.0f}%\n"
                        if treatment.restrictions:
                            diagnosis_report += f"     Restrictions: {', '.join(treatment.restrictions)}\n"
                
                # Prevention
                if disease.prevention_methods:
                    diagnosis_report += "\n   MÉTHODES DE PRÉVENTION:\n"
                    for method in disease.prevention_methods:
                        diagnosis_report += f"   - {method}\n"
                
                diagnosis_report += "\n" + "-" * 40 + "\n\n"
            
            # Add general advice
            diagnosis_report += "CONSEILS GÉNÉRAUX:\n"
            diagnosis_report += "- Surveillez régulièrement vos cultures\n"
            diagnosis_report += "- Intervenez rapidement en cas de détection\n"
            diagnosis_report += "- Respectez les doses et délais d'emploi\n"
            diagnosis_report += "- Consultez un expert en cas de doute\n"
            
            return diagnosis_report
            
        except Exception as e:
            logger.error(f"Error in disease diagnosis: {e}")
            return f"Erreur lors du diagnostic pour {crop_type}: {str(e)}. Veuillez reformuler votre demande."
    
    def _parse_symptoms(self, symptoms_text: str) -> List[str]:
        """Parse symptoms from text input."""
        # Split by common separators and clean up
        symptoms = re.split(r'[,;\.\n]', symptoms_text.lower())
        symptoms = [s.strip() for s in symptoms if s.strip()]
        
        # Remove common words that don't add value
        stop_words = ['et', 'ou', 'avec', 'sur', 'dans', 'de', 'la', 'le', 'les', 'des', 'du', 'de la']
        symptoms = [s for s in symptoms if s not in stop_words and len(s) > 2]
        
        return symptoms
    
    async def _arun(self, crop_type: str, symptoms: str, location: str) -> str:
        """Async version of disease diagnosis."""
        return self._run(crop_type, symptoms, location)


class PestIdentificationTool(BaseTool):
    """Tool for identifying crop pests."""
    
    name: str = "pest_identification"
    description: str = "Identifier les ravageurs et insectes nuisibles sur les cultures"
    
    def _run(self, crop_type: str, pest_description: str, damage_type: str) -> str:
        """Identify crop pests using the French pest database."""
        try:
            # Parse symptoms from the input
            symptoms = [pest_description, damage_type]
            symptoms = [s.strip() for s in symptoms if s.strip()]
            
            # Find matching pests
            matching_pests = pest_db.find_pests_by_symptoms(crop_type, symptoms)
            
            if not matching_pests:
                return f"Aucun ravageur identifié pour {crop_type} avec la description: {pest_description}. Vérifiez la description ou consultez un expert."
            
            # Build identification report
            identification_report = f"IDENTIFICATION DES RAVAGEURS SUR {crop_type.upper()}\n"
            identification_report += "=" * 50 + "\n\n"
            
            for i, pest in enumerate(matching_pests[:3], 1):  # Top 3 matches
                identification_report += f"{i}. {pest.name.upper()} ({pest.scientific_name})\n"
                identification_report += f"   Sévérité: {pest.severity.value}\n"
                identification_report += f"   Impact économique: {pest.economic_impact}\n\n"
                
                # Symptoms
                identification_report += "   SYMPTÔMES OBSERVÉS:\n"
                for symptom in pest.symptoms:
                    identification_report += f"   - {symptom.description}\n"
                
                # Threshold levels
                if pest.threshold_levels:
                    identification_report += "\n   SEUILS D'INTERVENTION:\n"
                    for stage, threshold in pest.threshold_levels.items():
                        identification_report += f"   - {stage}: {threshold}\n"
                
                # Treatments
                if pest.treatments:
                    identification_report += "\n   TRAITEMENTS RECOMMANDÉS:\n"
                    for treatment in pest.treatments[:2]:  # Top 2 treatments
                        identification_report += f"   - {treatment.name} ({treatment.active_ingredient})\n"
                        identification_report += f"     Dosage: {treatment.dosage}\n"
                        identification_report += f"     Timing: {treatment.application_timing}\n"
                        identification_report += f"     Efficacité: {treatment.effectiveness*100:.0f}%\n"
                        if treatment.restrictions:
                            identification_report += f"     Restrictions: {', '.join(treatment.restrictions)}\n"
                
                # Prevention
                if pest.prevention_methods:
                    identification_report += "\n   MÉTHODES DE PRÉVENTION:\n"
                    for method in pest.prevention_methods:
                        identification_report += f"   - {method}\n"
                
                identification_report += "\n" + "-" * 40 + "\n\n"
            
            # Add general advice
            identification_report += "CONSEILS GÉNÉRAUX:\n"
            identification_report += "- Surveillez régulièrement vos cultures\n"
            identification_report += "- Respectez les seuils d'intervention\n"
            identification_report += "- Privilégiez la lutte biologique quand possible\n"
            identification_report += "- Respectez les doses et délais d'emploi\n"
            
            return identification_report
            
        except Exception as e:
            logger.error(f"Error in pest identification: {e}")
            return f"Erreur lors de l'identification des ravageurs pour {crop_type}: {str(e)}. Veuillez reformuler votre demande."
    
    async def _arun(self, crop_type: str, pest_description: str, damage_type: str) -> str:
        """Async version of pest identification."""
        return self._run(crop_type, pest_description, damage_type)


class NutrientDeficiencyTool(BaseTool):
    """Tool for identifying nutrient deficiencies."""
    
    name: str = "nutrient_deficiency_analysis"
    description: str = "Analyser les carences nutritionnelles des cultures"
    
    def _run(self, crop_type: str, symptoms: str, growth_stage: str) -> str:
        """Analyze nutrient deficiencies using the French deficiency database."""
        try:
            # Parse symptoms from the input string
            symptom_list = self._parse_symptoms(symptoms)
            
            # Find matching deficiencies
            matching_deficiencies = deficiency_db.find_deficiencies_by_symptoms(crop_type, symptom_list)
            
            if not matching_deficiencies:
                return f"Aucune carence identifiée pour {crop_type} avec les symptômes: {symptoms}. Vérifiez la description des symptômes ou consultez un expert."
            
            # Build deficiency analysis report
            analysis_report = f"ANALYSE DES CARENCES POUR {crop_type.upper()} AU STADE {growth_stage.upper()}\n"
            analysis_report += "=" * 60 + "\n\n"
            
            for i, deficiency in enumerate(matching_deficiencies[:3], 1):  # Top 3 matches
                analysis_report += f"{i}. {deficiency.name.upper()} ({deficiency.nutrient_symbol})\n"
                analysis_report += f"   Type: {deficiency.nutrient_type.value}\n"
                analysis_report += f"   Sévérité: {deficiency.severity.value}\n"
                analysis_report += f"   Impact économique: {deficiency.economic_impact}\n\n"
                
                # Symptoms
                analysis_report += "   SYMPTÔMES OBSERVÉS:\n"
                for symptom in deficiency.symptoms:
                    analysis_report += f"   - {symptom.description}\n"
                
                # Fertilizer recommendations
                if deficiency.fertilizers:
                    analysis_report += "\n   RECOMMANDATIONS DE FERTILISATION:\n"
                    for fertilizer in deficiency.fertilizers[:2]:  # Top 2 fertilizers
                        analysis_report += f"   - {fertilizer.name} ({fertilizer.nutrient_content})\n"
                        analysis_report += f"     Dosage: {fertilizer.dosage}\n"
                        analysis_report += f"     Timing: {fertilizer.application_timing}\n"
                        analysis_report += f"     Méthode: {fertilizer.application_method}\n"
                        analysis_report += f"     Efficacité: {fertilizer.effectiveness*100:.0f}%\n"
                        if fertilizer.restrictions:
                            analysis_report += f"     Restrictions: {', '.join(fertilizer.restrictions)}\n"
                
                # Prevention
                if deficiency.prevention_methods:
                    analysis_report += "\n   MÉTHODES DE PRÉVENTION:\n"
                    for method in deficiency.prevention_methods:
                        analysis_report += f"   - {method}\n"
                
                analysis_report += "\n" + "-" * 40 + "\n\n"
            
            # Add general advice
            analysis_report += "CONSEILS GÉNÉRAUX:\n"
            analysis_report += "- Effectuez une analyse de sol régulière\n"
            analysis_report += "- Respectez les doses de fertilisation\n"
            analysis_report += "- Privilégiez la fertilisation organique\n"
            analysis_report += "- Surveillez l'équilibre des nutriments\n"
            
            return analysis_report
            
        except Exception as e:
            logger.error(f"Error in nutrient deficiency analysis: {e}")
            return f"Erreur lors de l'analyse des carences pour {crop_type}: {str(e)}. Veuillez reformuler votre demande."
    
    def _parse_symptoms(self, symptoms_text: str) -> List[str]:
        """Parse symptoms from text input."""
        # Split by common separators and clean up
        symptoms = re.split(r'[,;\.\n]', symptoms_text.lower())
        symptoms = [s.strip() for s in symptoms if s.strip()]
        
        # Remove common words that don't add value
        stop_words = ['et', 'ou', 'avec', 'sur', 'dans', 'de', 'la', 'le', 'les', 'des', 'du', 'de la']
        symptoms = [s for s in symptoms if s not in stop_words and len(s) > 2]
        
        return symptoms
    
    async def _arun(self, crop_type: str, symptoms: str, growth_stage: str) -> str:
        """Async version of nutrient deficiency analysis."""
        return self._run(crop_type, symptoms, growth_stage)


class TreatmentRecommendationTool(BaseTool):
    """Tool for recommending treatments."""
    
    name: str = "treatment_recommendation"
    description: str = "Recommander des traitements pour les problèmes de santé des cultures"
    
    def _run(self, problem_type: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Recommend treatments based on problem type and crop stage."""
        try:
            # Determine if it's a disease, pest, or deficiency
            problem_category = self._categorize_problem(problem_type)
            
            if problem_category == "disease":
                return self._get_disease_treatments(problem_type, crop_type, severity, growth_stage)
            elif problem_category == "pest":
                return self._get_pest_treatments(problem_type, crop_type, severity, growth_stage)
            elif problem_category == "deficiency":
                return self._get_deficiency_treatments(problem_type, crop_type, severity, growth_stage)
            else:
                return self._get_general_treatments(problem_type, crop_type, severity, growth_stage)
                
        except Exception as e:
            logger.error(f"Error in treatment recommendation: {e}")
            return f"Erreur lors des recommandations de traitement pour {problem_type}: {str(e)}. Veuillez reformuler votre demande."
    
    def _categorize_problem(self, problem_type: str) -> str:
        """Categorize the problem type."""
        problem_lower = problem_type.lower()
        
        # Disease keywords
        disease_keywords = ["maladie", "champignon", "bactérie", "virus", "septoriose", "oïdium", "rouille", "sclérotinia"]
        if any(keyword in problem_lower for keyword in disease_keywords):
            return "disease"
        
        # Pest keywords
        pest_keywords = ["ravageur", "insecte", "puceron", "cécidomyie", "pyrale", "altise", "chenille"]
        if any(keyword in problem_lower for keyword in pest_keywords):
            return "pest"
        
        # Deficiency keywords
        deficiency_keywords = ["carence", "déficience", "azote", "phosphore", "potassium", "magnésium", "fer"]
        if any(keyword in problem_lower for keyword in deficiency_keywords):
            return "deficiency"
        
        return "unknown"
    
    def _get_disease_treatments(self, disease_name: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Get disease treatment recommendations."""
        # Find the disease in the database
        disease = disease_db.diseases.get(disease_name.lower())
        if not disease:
            # Try to find by partial match
            for name, disease_obj in disease_db.diseases.items():
                if disease_name.lower() in name or name in disease_name.lower():
                    disease = disease_obj
                    break
        
        if not disease:
            return f"Maladie '{disease_name}' non trouvée dans la base de données. Vérifiez le nom ou consultez un expert."
        
        # Build treatment recommendations
        treatment_report = f"RECOMMANDATIONS DE TRAITEMENT POUR {disease_name.upper()}\n"
        treatment_report += f"Culture: {crop_type.upper()} | Sévérité: {severity.upper()} | Stade: {growth_stage.upper()}\n"
        treatment_report += "=" * 60 + "\n\n"
        
        # Get treatments
        treatments = disease.treatments
        if not treatments:
            treatment_report += "Aucun traitement spécifique disponible pour cette maladie.\n"
            treatment_report += "Consultez un expert ou un conseiller agricole.\n"
            return treatment_report
        
        treatment_report += "TRAITEMENTS RECOMMANDÉS:\n\n"
        
        for i, treatment in enumerate(treatments[:3], 1):  # Top 3 treatments
            treatment_report += f"{i}. {treatment.name.upper()}\n"
            treatment_report += f"   Principe actif: {treatment.active_ingredient}\n"
            treatment_report += f"   Dosage: {treatment.dosage}\n"
            treatment_report += f"   Timing: {treatment.application_timing}\n"
            treatment_report += f"   Efficacité: {treatment.effectiveness*100:.0f}%\n"
            treatment_report += f"   AMM: {treatment.amm_number}\n"
            
            if treatment.restrictions:
                treatment_report += f"   Restrictions: {', '.join(treatment.restrictions)}\n"
            
            treatment_report += "\n"
        
        # Add general advice
        treatment_report += "CONSEILS GÉNÉRAUX:\n"
        treatment_report += "- Respectez les doses et délais d'emploi\n"
        treatment_report += "- Alternez les matières actives pour éviter les résistances\n"
        treatment_report += "- Privilégiez les traitements préventifs\n"
        treatment_report += "- Surveillez l'efficacité du traitement\n"
        
        return treatment_report
    
    def _get_pest_treatments(self, pest_name: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Get pest treatment recommendations."""
        # Find the pest in the database
        pest = pest_db.pests.get(pest_name.lower())
        if not pest:
            # Try to find by partial match
            for name, pest_obj in pest_db.pests.items():
                if pest_name.lower() in name or name in pest_name.lower():
                    pest = pest_obj
                    break
        
        if not pest:
            return f"Ravageur '{pest_name}' non trouvé dans la base de données. Vérifiez le nom ou consultez un expert."
        
        # Build treatment recommendations
        treatment_report = f"RECOMMANDATIONS DE TRAITEMENT POUR {pest_name.upper()}\n"
        treatment_report += f"Culture: {crop_type.upper()} | Sévérité: {severity.upper()} | Stade: {growth_stage.upper()}\n"
        treatment_report += "=" * 60 + "\n\n"
        
        # Get treatments
        treatments = pest.treatments
        if not treatments:
            treatment_report += "Aucun traitement spécifique disponible pour ce ravageur.\n"
            treatment_report += "Consultez un expert ou un conseiller agricole.\n"
            return treatment_report
        
        treatment_report += "TRAITEMENTS RECOMMANDÉS:\n\n"
        
        for i, treatment in enumerate(treatments[:3], 1):  # Top 3 treatments
            treatment_report += f"{i}. {treatment.name.upper()}\n"
            treatment_report += f"   Principe actif: {treatment.active_ingredient}\n"
            treatment_report += f"   Dosage: {treatment.dosage}\n"
            treatment_report += f"   Timing: {treatment.application_timing}\n"
            treatment_report += f"   Efficacité: {treatment.effectiveness*100:.0f}%\n"
            treatment_report += f"   AMM: {treatment.amm_number}\n"
            
            if treatment.restrictions:
                treatment_report += f"   Restrictions: {', '.join(treatment.restrictions)}\n"
            
            treatment_report += "\n"
        
        # Add threshold information
        if pest.threshold_levels:
            treatment_report += "SEUILS D'INTERVENTION:\n"
            for stage, threshold in pest.threshold_levels.items():
                treatment_report += f"- {stage}: {threshold}\n"
            treatment_report += "\n"
        
        # Add general advice
        treatment_report += "CONSEILS GÉNÉRAUX:\n"
        treatment_report += "- Respectez les seuils d'intervention\n"
        treatment_report += "- Privilégiez la lutte biologique\n"
        treatment_report += "- Alternez les matières actives\n"
        treatment_report += "- Surveillez l'efficacité du traitement\n"
        
        return treatment_report
    
    def _get_deficiency_treatments(self, deficiency_name: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Get deficiency treatment recommendations."""
        # Find the deficiency in the database
        deficiency = deficiency_db.deficiencies.get(deficiency_name.lower())
        if not deficiency:
            # Try to find by partial match
            for name, deficiency_obj in deficiency_db.deficiencies.items():
                if deficiency_name.lower() in name or name in deficiency_name.lower():
                    deficiency = deficiency_obj
                    break
        
        if not deficiency:
            return f"Carence '{deficiency_name}' non trouvée dans la base de données. Vérifiez le nom ou consultez un expert."
        
        # Build treatment recommendations
        treatment_report = f"RECOMMANDATIONS DE FERTILISATION POUR {deficiency_name.upper()}\n"
        treatment_report += f"Culture: {crop_type.upper()} | Sévérité: {severity.upper()} | Stade: {growth_stage.upper()}\n"
        treatment_report += "=" * 60 + "\n\n"
        
        # Get fertilizers
        fertilizers = deficiency.fertilizers
        if not fertilizers:
            treatment_report += "Aucune recommandation de fertilisation disponible.\n"
            treatment_report += "Consultez un expert ou un conseiller agricole.\n"
            return treatment_report
        
        treatment_report += "FERTILISANTS RECOMMANDÉS:\n\n"
        
        for i, fertilizer in enumerate(fertilizers[:3], 1):  # Top 3 fertilizers
            treatment_report += f"{i}. {fertilizer.name.upper()}\n"
            treatment_report += f"   Teneur: {fertilizer.nutrient_content}\n"
            treatment_report += f"   Dosage: {fertilizer.dosage}\n"
            treatment_report += f"   Timing: {fertilizer.application_timing}\n"
            treatment_report += f"   Méthode: {fertilizer.application_method}\n"
            treatment_report += f"   Efficacité: {fertilizer.effectiveness*100:.0f}%\n"
            
            if fertilizer.restrictions:
                treatment_report += f"   Restrictions: {', '.join(fertilizer.restrictions)}\n"
            
            treatment_report += "\n"
        
        # Add general advice
        treatment_report += "CONSEILS GÉNÉRAUX:\n"
        treatment_report += "- Effectuez une analyse de sol\n"
        treatment_report += "- Respectez les doses de fertilisation\n"
        treatment_report += "- Privilégiez la fertilisation organique\n"
        treatment_report += "- Surveillez l'équilibre des nutriments\n"
        
        return treatment_report
    
    def _get_general_treatments(self, problem_type: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Get general treatment recommendations."""
        treatment_report = f"RECOMMANDATIONS GÉNÉRALES POUR {problem_type.upper()}\n"
        treatment_report += f"Culture: {crop_type.upper()} | Sévérité: {severity.upper()} | Stade: {growth_stage.upper()}\n"
        treatment_report += "=" * 60 + "\n\n"
        
        treatment_report += "CONSEILS GÉNÉRAUX:\n"
        treatment_report += "- Identifiez précisément le problème\n"
        treatment_report += "- Consultez un expert ou un conseiller agricole\n"
        treatment_report += "- Respectez les bonnes pratiques agricoles\n"
        treatment_report += "- Surveillez régulièrement vos cultures\n"
        treatment_report += "- Documentez les interventions\n"
        
        return treatment_report
    
    async def _arun(self, problem_type: str, crop_type: str, severity: str, growth_stage: str) -> str:
        """Async version of treatment recommendations."""
        return self._run(problem_type, crop_type, severity, growth_stage)


class CropHealthMonitorAgent(IntegratedAgriculturalAgent):
    """
    Crop Health Monitor Agent - Specialized in crop health diagnosis and monitoring.
    """
    
    def __init__(self, **kwargs):
        # Initialize tools
        tools = [
            DiseaseDiagnosisTool(),
            PestIdentificationTool(),
            NutrientDeficiencyTool(),
            TreatmentRecommendationTool()
        ]
        
        super().__init__(
            name="crop_health",
            description="Spécialiste de la santé des cultures françaises",
            system_prompt="",  # Will be set dynamically
            tools=tools,
            **kwargs
        )
        
        logger.info("Initialized Crop Health Monitor Agent")
    
    def get_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get the system prompt for Crop Health Monitor."""
        return FrenchAgriculturalPrompts.get_crop_health_prompt(context)
    
    def process_message(
        self, 
        message: str, 
        state: AgentState,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return agent response with tool orchestration.
        """
        try:
            # Update context with state information
            if not context:
                context = {}
            
            context.update({
                'user_id': state.user_id,
                'farm_id': state.farm_id,
                'current_agent': self.name
            })
            
            # Determine which tools to use based on message content
            tools_to_use = self._determine_tools_needed(message)
            tool_results = []
            
            # Execute relevant tools
            for tool_name in tools_to_use:
                tool_result = self._execute_tool(tool_name, message, context)
                if tool_result:
                    tool_results.append(tool_result)
            
            # Get system prompt with context
            system_prompt = self.get_system_prompt(context)
            
            # Add message to memory
            self.memory.chat_memory.add_user_message(message)
            
            # Prepare messages for LLM with tool results
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add tool results to context
            if tool_results:
                tool_context = "\n\nRÉSULTATS DES OUTILS SPÉCIALISÉS:\n"
                for i, result in enumerate(tool_results, 1):
                    tool_context += f"\n--- Résultat {i} ---\n{result}\n"
                messages.append({"role": "assistant", "content": tool_context})
            
            # Add conversation history
            chat_history = self.memory.chat_memory.messages[-6:]  # Last 6 messages
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Generate response
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Add response to memory
            self.memory.chat_memory.add_ai_message(response_text)
            
            # Update state
            state.messages.append(HumanMessage(content=message))
            state.messages.append(AIMessage(content=response_text))
            state.current_agent = self.name
            
            # Format response
            metadata = {
                "agent_type": "crop_health",
                "tools_used": tools_to_use,
                "context_used": context,
                "memory_summary": self.get_memory_summary()
            }
            
            return self.format_response(response_text, metadata)
            
        except Exception as e:
            logger.error(f"Error processing message in Crop Health Monitor: {e}")
            error_response = "Je rencontre une difficulté technique. Pouvez-vous reformuler votre question ?"
            return self.format_response(error_response, {"error": str(e)})
    
    def _determine_tools_needed(self, message: str) -> List[str]:
        """Determine which tools to use based on message content."""
        message_lower = message.lower()
        tools_needed = []
        
        # Disease-related keywords
        disease_keywords = ["maladie", "champignon", "bactérie", "virus", "septoriose", "oïdium", "rouille", "sclérotinia", "taches", "pourriture"]
        if any(keyword in message_lower for keyword in disease_keywords):
            tools_needed.append("disease_diagnosis")
        
        # Pest-related keywords
        pest_keywords = ["ravageur", "insecte", "puceron", "cécidomyie", "pyrale", "altise", "chenille", "trous", "galeries", "miellat"]
        if any(keyword in message_lower for keyword in pest_keywords):
            tools_needed.append("pest_identification")
        
        # Deficiency-related keywords
        deficiency_keywords = ["carence", "déficience", "azote", "phosphore", "potassium", "magnésium", "fer", "jaunissement", "décoloration"]
        if any(keyword in message_lower for keyword in deficiency_keywords):
            tools_needed.append("nutrient_deficiency_analysis")
        
        # Treatment-related keywords
        treatment_keywords = ["traitement", "produit", "dose", "pulvérisation", "fertilisation", "engrais", "amm", "efficacité"]
        if any(keyword in message_lower for keyword in treatment_keywords):
            tools_needed.append("treatment_recommendation")
        
        return tools_needed
    
    def _execute_tool(self, tool_name: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Execute a specific tool based on the message content."""
        try:
            # Find the tool
            tool = None
            for t in self.tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                return None
            
            # Extract parameters from message for each tool
            if tool_name == "disease_diagnosis":
                crop_type = self._extract_crop_type(message)
                symptoms = self._extract_symptoms(message)
                location = context.get("location", "France")
                return tool._run(crop_type, symptoms, location)
            
            elif tool_name == "pest_identification":
                crop_type = self._extract_crop_type(message)
                pest_description = self._extract_pest_description(message)
                damage_type = self._extract_damage_type(message)
                return tool._run(crop_type, pest_description, damage_type)
            
            elif tool_name == "nutrient_deficiency_analysis":
                crop_type = self._extract_crop_type(message)
                symptoms = self._extract_symptoms(message)
                growth_stage = self._extract_growth_stage(message)
                return tool._run(crop_type, symptoms, growth_stage)
            
            elif tool_name == "treatment_recommendation":
                problem_type = self._extract_problem_type(message)
                crop_type = self._extract_crop_type(message)
                severity = self._extract_severity(message)
                growth_stage = self._extract_growth_stage(message)
                return tool._run(problem_type, crop_type, severity, growth_stage)
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return None
    
    def _extract_crop_type(self, message: str) -> str:
        """Extract crop type from message."""
        crop_types = ["blé", "orge", "maïs", "colza", "tournesol", "triticale"]
        message_lower = message.lower()
        
        for crop in crop_types:
            if crop in message_lower:
                return crop
        
        return "blé"  # Default
    
    def _extract_symptoms(self, message: str) -> str:
        """Extract symptoms from message."""
        # This is a simplified extraction - in reality, you'd use NLP
        return message
    
    def _extract_pest_description(self, message: str) -> str:
        """Extract pest description from message."""
        return message
    
    def _extract_damage_type(self, message: str) -> str:
        """Extract damage type from message."""
        return "dégâts observés"
    
    def _extract_growth_stage(self, message: str) -> str:
        """Extract growth stage from message."""
        stages = ["germination", "tallage", "montaison", "épiaison", "floraison", "maturité"]
        message_lower = message.lower()
        
        for stage in stages:
            if stage in message_lower:
                return stage
        
        return "montaison"  # Default
    
    def _extract_problem_type(self, message: str) -> str:
        """Extract problem type from message."""
        return message
    
    def _extract_severity(self, message: str) -> str:
        """Extract severity from message."""
        severity_keywords = {
            "faible": ["faible", "léger", "peu"],
            "modérée": ["modéré", "moyen", "modérément"],
            "élevée": ["élevé", "fort", "important"],
            "critique": ["critique", "grave", "sévère"]
        }
        
        message_lower = message.lower()
        for severity, keywords in severity_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return severity
        
        return "modérée"  # Default
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the context contains required information.
        """
        # Crop health agent can work with minimal context
        return True
    
    def diagnose_crop_problem(self, crop_type: str, symptoms: str, location: str) -> str:
        """
        Diagnose crop health problems.
        """
        # TODO: Implement actual crop problem diagnosis
        return f"Diagnostic pour {crop_type} à {location}: analyse des symptômes et recommandations de traitement"
    
    def identify_pests(self, crop_type: str, pest_description: str) -> str:
        """
        Identify crop pests.
        """
        # TODO: Implement actual pest identification
        return f"Identification des ravageurs sur {crop_type}: espèces identifiées et seuils d'intervention"
    
    def analyze_nutrient_deficiency(self, crop_type: str, symptoms: str) -> str:
        """
        Analyze nutrient deficiencies.
        """
        # TODO: Implement actual nutrient deficiency analysis
        return f"Analyse des carences pour {crop_type}: carences identifiées et recommandations de fertilisation"
    
    def recommend_treatment(self, problem_type: str, crop_type: str, severity: str) -> str:
        """
        Recommend treatments for crop problems.
        """
        # TODO: Implement actual treatment recommendations
        return f"Recommandations de traitement pour {problem_type} sur {crop_type}: produits, doses et précautions"
    
    def get_disease_forecast(self, crop_type: str, location: str, weather_conditions: str) -> str:
        """
        Get disease forecast based on weather conditions.
        """
        # TODO: Implement actual disease forecasting
        return f"Prévision des maladies pour {crop_type} à {location}: risque basé sur les conditions météo"
