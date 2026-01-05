"""
AI Service for generating personalised study roadmaps using Claude API .

This module handles:
- Claude API communication
- Prompt engineering for roadmap generation
- JSON parsing and validation
- Error handling
"""

import os
import json
import anthropic
from typing import Dict, List, Optional
from datetime import date


class RoadmapGenerationError(Exception):
    """Custom exception for roadmap generation failures"""
    pass


class AIRoadmapService:
    """Service for generating AI-powered study roadmaps"""

    def __init__(self):
        """Initialise the Claude API client"""
        api_key = os.getenv('API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please add it to your .env file"
            )
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514" # Latest Sonnet model

    def generate_roadmap(
            self,
            subject_name: str,
            current_level: str,
            target_level: str,
            strengths: List[str],
            weaknesses: List[str],
            areas_to_improve: List[str],
            deadline: date,
            study_hours_logged: float = 0.0
    ) -> Dict:
        """
        Generate a personalised study roadmap using Cluade AI.

        Args:
            subject_name: Name of the subject (e.g., "Mathematics")
            current_level: Current grade/level (e.g., "Grade 5")
            target_level: Target grade/level (e.g., "Grade 7")
            strengths: List of student strengths from feedback
            weaknesses: List of student weaknesses from feedback
            areas_to_improve: List of specific areas to work on
            deadline: Goal deadline date
            study_Hours_logged: Total hours already studied

        Returns:
            Dict containing roadmap data with steps and checklist

        Raises:
            RoadmapGenerationError: If generation fails
        """

        # Build the prompt
        prompt = self._build_prompt(
            subject_name=subject_name,
            current_level=current_level,
            target_level=target_level,
            strengths=strengths,
            weaknesses=weaknesses,
            areas_to_improve=areas_to_improve,
            deadline=deadline,
            study_hours_logged=study_hours_logged
        )

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7, # Balanced creativity
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text response
            response_text = response.content[0].text

            # Parse JSON from response
            roadmap_data = self._parse_response(response_text)

            # Validate structure
            self._validate_roadmap(roadmap_data)

            return roadmap_data
        
        except anthropic.APIError as e:
            raise RoadmapGenerationError(f"Claude API error: {str(e)}")
        except json.JSONDecodeError as e:
            raise RoadmapGenerationError(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            raise RoadmapGenerationError(f"Unexpected error: {str(e)}")
        
    def _build_prompt(
            self,
            subject_name: str,
            current_level: str,
            target_level: str,
            strengths: List[str],
            weaknesses: List[str],
            areas_to_improve: List[str],
            deadline: date,
            study_hours_logged: float
    ) -> str:
        """Build the prompt for Claude API"""

        # Calculate days until deadline
        days_remaining = (deadline - date.today()).days

        # Format lists
        strengths_text = "\n".join(f"- {s}" for s in strengths) if strengths else "- No strengths recorded yet"
        weaknesses_text = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "- No weaknesses recorded yet"
        areas_text = "\n".join(f"- {a}" for a in areas_to_improve) if areas_to_improve else "- No specific areas noted"

        prompt = f"""You are an expert GCSE study planner. Create a personalised study roadmap for a Year 9 student.

STUDENT CONTEXT:
Subject: {subject_name}
Current Level: {current_level}
Target Level: {target_level}
Deadline: {deadline.strftime('%B %d %Y')} ({days_remaining} days remaining)
Study Hours Logged: {study_hours_logged} hours

TEACHER FEEDBACK:
Strengths:
{strengths_text}

Weaknesses:
{weaknesses_text}

Areas to Improve:
{areas_text}

YOUR TASK:
Create a study roadmap with 4-6 steps to help this student improve from {current_level} to {target_level}.

REQUIREMENTS:
1. Each step should be specific and actionable
2. Prioritise addressing weaknesses while building on strengths
3. Include a mix of categories:
    - "weakness" (address weak areas)
    - "strength" (build on strong areas)
    - "level_up" (advanced skills for target level)
4. Assign realistic difficulty levels (easy/medium/hard)
5. Estimate hours needed for each step (5-15 hours)
6. For each step, include 3-5 specific checklist items
7. Consider the deadlien when planning

OUTPUT FORMAT:
Respond ONLY with a JSON object (no markdown, no explanation). Use this exact structure:

{{
    "title": "Brief title for the roadmap (e.g., 'Mathematics Grade 5 → 7 Plan')",
    "overview": "2-3 sentence overview explaining the strategy",
    "steps": [
        {{
        "order": 1,
        "title": "Step title (concise, actionable)",
        "description": "Detailed explanation of what this step covers and why it's important",
        "category": "weakness|strength|level_up",
        "difficulty": "easy|medium|hard",
        "estimated_hours": 8,
        "checklist": [
        "Specific action item 1",
        "Specific action item 2",
        "Specific action item 3",
        ]
        }}
    ]
}}

IMPORTANT:
- Create exactly 4-6 steps
- Each step should have 3-5 checklist items
- Be specific to the subject and student's needs
- Make it realistic and achievable within the timeframe
- Focus on exam success (GCSE-specific strategies)
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse JSON from Claude's response"""

        # Try to extract JSON from response
        # Sometimes Claude adds markdown formatting
        text = response_text.strip()

        # Remove markdown code fences if present
        if text.startswith("```json"):
            text = text[7:] # Remove ```json
        if text.startswith("```"):
            text = text[3:] # Remove ```
        if text.endswith("```"):
            text = text[:-3] # Remove ```

        text = text.strip()

        # Parse JSON
        return  json.loads(text)
    
    def _validate_roadmap(self, roadmap_data: Dict) -> None:
        """Validate the roadmap structure"""

        required_fields = ['title', 'overview', 'steps']
        for field in required_fields:
            if field not in roadmap_data:
                raise RoadmapGenerationError(f"Missing required field: {field}")
            
        if not isinstance(roadmap_data['steps'], list):
            raise RoadmapGenerationError("Steps must be a list")
        
        if len(roadmap_data['steps']) < 3 or len(roadmap_data['steps']) > 8:
            raise RoadmapGenerationError(
                f"Expected 4-6 steps, got {len(roadmap_data['steps'])}"
            )
        
        # Validate each step
        required_step_fields = [
            'order', 'title', 'description', 'category',
            'difficulty', 'estimated_hours', 'checklist'
        ]

        valid_categories = ['weakness', 'strength', 'level_up']
        valid_difficulties = ['easy', 'medium', 'hard']

        for i, step in enumerate(roadmap_data['steps']):
            # Check required fields
            for field in required_step_fields:
                if field not in step:
                    raise RoadmapGenerationError(
                        f"Step {i+1} missing required field: {field}"
                    )
                
            # Validate category
            if step['category'] not in valid_categories:
                raise RoadmapGenerationError(
                    f"Step {i+1} has invalid category: {step['category']}"
                )
            
            # Validate difficulty
            if step['difficulty'] not in valid_difficulties:
                raise RoadmapGenerationError(
                    f"Step {i+1} has invalid difficulty: {step['difficulty']}"
                )
            
            # Validate checklist
            if not isinstance(step['checklist'], list):
                raise RoadmapGenerationError(
                    f"Step {i+1} checklist must be a list"
                )
            
            if len(step['checklist']) < 2 or len(step['checklist']) > 7:
                raise RoadmapGenerationError(
                    f"Step {i+1} should have 3-5 checklist items"
                )
            

# Singleton instnace
_ai_service = None

def get_ai_service() -> AIRoadmapService:
    """Fet or create the AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIRoadmapService()
    return _ai_service