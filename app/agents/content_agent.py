from crewai import Agent, Task
from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class TextGeneratorTool(BaseTool):
    name: str = "text_generator"
    description: str = "Generates various types of text content based on prompts and specifications"
    
    def _run(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text content"""
        try:
            content_type = generation_request.get("type", "general")
            prompt = generation_request.get("prompt", "")
            tone = generation_request.get("tone", "professional")
            length = generation_request.get("length", "medium")
            
            # Generate content based on type and parameters
            generated_content = self._generate_content(content_type, prompt, tone, length)
            
            result = {
                "generated": True,
                "content": generated_content,
                "type": content_type,
                "word_count": len(generated_content.split()),
                "character_count": len(generated_content),
                "tone": tone,
                "message": f"{content_type.title()} content generated successfully"
            }
            
            logger.info(f"Text content generated: {content_type}, {len(generated_content)} chars")
            return result
            
        except Exception as e:
            logger.error(f"Error generating text content: {e}")
            return {"generated": False, "error": str(e)}
    
    def _generate_content(self, content_type: str, prompt: str, tone: str, length: str) -> str:
        """Generate content based on parameters"""
        
        if content_type == "email":
            return self._generate_email(prompt, tone)
        elif content_type == "letter":
            return self._generate_letter(prompt, tone)
        elif content_type == "summary":
            return self._generate_summary(prompt, length)
        elif content_type == "creative":
            return self._generate_creative_content(prompt, tone)
        elif content_type == "business":
            return self._generate_business_content(prompt, tone)
        else:
            return self._generate_general_content(prompt, tone, length)
    
    def _generate_email(self, prompt: str, tone: str) -> str:
        if "meeting" in prompt.lower():
            return f"""Subject: Meeting Request

Dear Colleague,

I hope this email finds you well. I would like to schedule a meeting to discuss {prompt.lower().replace('meeting about', '').replace('meeting for', '').strip()}.

Please let me know your availability for the upcoming week, and I'll send a calendar invitation.

Best regards,
[Your Name]"""
        
        return f"""Subject: {prompt.title()}

Dear Recipient,

I'm writing regarding {prompt.lower()}.

{self._get_tone_content(tone)}

Please let me know if you need any additional information.

Best regards,
[Your Name]"""
    
    def _generate_letter(self, prompt: str, tone: str) -> str:
        return f"""Dear Recipient,

I am writing to you concerning {prompt.lower()}.

{self._get_tone_content(tone)}

Thank you for your time and consideration.

Sincerely,
[Your Name]
[Date]"""
    
    def _generate_summary(self, prompt: str, length: str) -> str:
        if "short" in length.lower():
            return f"Summary: {prompt} - Key points identified and condensed into essential information."
        elif "long" in length.lower():
            return f"""Detailed Summary:

Subject: {prompt}

This comprehensive summary covers the main aspects of {prompt.lower()}. The key findings and important details have been organized to provide a clear understanding of the topic.

Main Points:
• Primary consideration: [Details about {prompt}]
• Secondary factors: [Supporting information]
• Conclusion: [Final thoughts and recommendations]

This summary provides a thorough overview while maintaining clarity and focus."""
        else:
            return f"Summary of {prompt}: Main points have been identified and organized for easy reference. Key information includes relevant details and important considerations."
    
    def _generate_creative_content(self, prompt: str, tone: str) -> str:
        return f"""Creative Content: {prompt.title()}

{self._get_creative_opening()}

{prompt} represents an opportunity for innovation and creativity. Through careful consideration and imaginative thinking, we can explore new possibilities and develop unique approaches.

{self._get_tone_content(tone)}

The creative process allows us to transform ideas into meaningful expressions that resonate with our intended audience."""
    
    def _generate_business_content(self, prompt: str, tone: str) -> str:
        return f"""Business Communication: {prompt.title()}

Executive Summary:
This document addresses {prompt.lower()} from a business perspective, focusing on strategic implications and operational considerations.

Key Objectives:
• Strategic alignment with business goals
• Operational efficiency and effectiveness
• Risk assessment and mitigation
• Performance measurement and optimization

{self._get_tone_content(tone)}

Recommended next steps include further analysis and stakeholder consultation to ensure successful implementation."""
    
    def _generate_general_content(self, prompt: str, tone: str, length: str) -> str:
        base_content = f"Regarding {prompt}, this content addresses the key aspects and provides relevant information."
        
        if "short" in length.lower():
            return f"{base_content} {self._get_tone_content(tone)}"
        elif "long" in length.lower():
            return f"""{base_content}

Detailed Analysis:
{prompt} requires careful consideration of multiple factors. Through systematic analysis, we can identify the most important elements and develop appropriate responses.

{self._get_tone_content(tone)}

Additional considerations include context, timing, and available resources. These factors contribute to the overall effectiveness of our approach.

Conclusion:
The information provided offers a comprehensive foundation for understanding and addressing {prompt.lower()}."""
        else:
            return f"{base_content} {self._get_tone_content(tone)} This provides a balanced perspective on the topic."
    
    def _get_tone_content(self, tone: str) -> str:
        if tone == "formal":
            return "This matter requires professional attention and careful consideration of all relevant factors."
        elif tone == "casual":
            return "Let's keep this simple and straightforward while covering what we need to address."
        elif tone == "friendly":
            return "I hope this information is helpful, and please feel free to reach out if you have any questions!"
        elif tone == "persuasive":
            return "This presents an excellent opportunity that deserves serious consideration and prompt action."
        else:  # professional (default)
            return "This information is provided to ensure clear communication and effective decision-making."
    
    def _get_creative_opening(self) -> str:
        return "Imagination and innovation come together to create something meaningful and engaging."

class EmailComposerTool(BaseTool):
    name: str = "email_composer"
    description: str = "Composes professional emails with proper formatting and etiquette"
    
    def _run(self, email_request: Dict[str, Any]) -> Dict[str, Any]:
        """Compose an email"""
        try:
            recipient = email_request.get("recipient", "Recipient")
            subject = email_request.get("subject", "Email Subject")
            purpose = email_request.get("purpose", "")
            tone = email_request.get("tone", "professional")
            include_attachment = email_request.get("include_attachment", False)
            
            # Compose the email
            email_content = self._compose_email(recipient, subject, purpose, tone, include_attachment)
            
            result = {
                "composed": True,
                "email_content": email_content,
                "subject": subject,
                "recipient": recipient,
                "tone": tone,
                "has_attachment": include_attachment,
                "message": "Email composed successfully"
            }
            
            logger.info(f"Email composed for {recipient}: {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Error composing email: {e}")
            return {"composed": False, "error": str(e)}
    
    def _compose_email(self, recipient: str, subject: str, purpose: str, tone: str, include_attachment: bool) -> str:
        greeting = f"Dear {recipient}," if tone == "formal" else f"Hi {recipient},"
        
        body = self._get_email_body(purpose, tone)
        
        attachment_note = "\n\nPlease find the attached document for your reference." if include_attachment else ""
        
        closing = self._get_email_closing(tone)
        
        return f"""Subject: {subject}

{greeting}

{body}{attachment_note}

{closing}
[Your Name]"""
    
    def _get_email_body(self, purpose: str, tone: str) -> str:
        if not purpose:
            purpose = "follow up on our previous conversation"
        
        if tone == "formal":
            return f"I am writing to {purpose.lower()}. I would appreciate your consideration of this matter."
        elif tone == "casual":
            return f"I wanted to reach out about {purpose.lower()}. Let me know what you think!"
        elif tone == "friendly":
            return f"I hope you're doing well! I wanted to touch base regarding {purpose.lower()}."
        else:  # professional
            return f"I am contacting you regarding {purpose.lower()}. Please let me know if you need any additional information."
    
    def _get_email_closing(self, tone: str) -> str:
        if tone == "formal":
            return "Respectfully yours,"
        elif tone == "casual":
            return "Thanks!"
        elif tone == "friendly":
            return "Best wishes,"
        else:  # professional
            return "Best regards,"

class IdeaBrainstormerTool(BaseTool):
    name: str = "idea_brainstormer"
    description: str = "Generates creative ideas and brainstorming suggestions"
    
    def _run(self, brainstorm_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brainstorming ideas"""
        try:
            topic = brainstorm_request.get("topic", "general brainstorming")
            quantity = brainstorm_request.get("quantity", 5)
            focus_area = brainstorm_request.get("focus_area", "general")
            
            # Generate ideas
            ideas = self._generate_ideas(topic, quantity, focus_area)
            
            result = {
                "brainstormed": True,
                "topic": topic,
                "ideas": ideas,
                "idea_count": len(ideas),
                "focus_area": focus_area,
                "message": f"Generated {len(ideas)} ideas for {topic}"
            }
            
            logger.info(f"Brainstormed {len(ideas)} ideas for: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error in brainstorming: {e}")
            return {"brainstormed": False, "error": str(e)}
    
    def _generate_ideas(self, topic: str, quantity: int, focus_area: str) -> List[Dict[str, str]]:
        """Generate creative ideas"""
        ideas = []
        base_ideas = self._get_base_ideas(topic, focus_area)
        
        for i in range(min(quantity, len(base_ideas))):
            idea = base_ideas[i]
            ideas.append({
                "id": i + 1,
                "title": idea["title"],
                "description": idea["description"],
                "category": focus_area,
                "feasibility": idea.get("feasibility", "medium")
            })
        
        return ideas
    
    def _get_base_ideas(self, topic: str, focus_area: str) -> List[Dict[str, str]]:
        """Get base ideas for different topics and focus areas"""
        
        if focus_area == "business":
            return [
                {"title": f"Digital Solution for {topic}", "description": "Leverage technology to streamline processes", "feasibility": "high"},
                {"title": f"Partnership Strategy", "description": "Collaborate with industry leaders", "feasibility": "medium"},
                {"title": f"Customer-Centric Approach", "description": "Focus on user experience improvements", "feasibility": "high"},
                {"title": f"Automation Implementation", "description": "Automate routine tasks and workflows", "feasibility": "medium"},
                {"title": f"Data-Driven Insights", "description": "Use analytics to inform decisions", "feasibility": "high"}
            ]
        elif focus_area == "creative":
            return [
                {"title": f"Interactive {topic} Experience", "description": "Create engaging user interactions", "feasibility": "medium"},
                {"title": f"Storytelling Approach", "description": "Use narrative to communicate ideas", "feasibility": "high"},
                {"title": f"Visual Innovation", "description": "Incorporate compelling visual elements", "feasibility": "medium"},
                {"title": f"Community Building", "description": "Foster user engagement and participation", "feasibility": "high"},
                {"title": f"Gamification Elements", "description": "Add game-like features for engagement", "feasibility": "medium"}
            ]
        elif focus_area == "technical":
            return [
                {"title": f"API Integration for {topic}", "description": "Connect with external services", "feasibility": "high"},
                {"title": f"Mobile-First Design", "description": "Optimize for mobile devices", "feasibility": "high"},
                {"title": f"Cloud Infrastructure", "description": "Leverage cloud services for scalability", "feasibility": "medium"},
                {"title": f"AI/ML Implementation", "description": "Use artificial intelligence capabilities", "feasibility": "low"},
                {"title": f"Real-time Processing", "description": "Enable live data processing and updates", "feasibility": "medium"}
            ]
        else:  # general
            return [
                {"title": f"Innovative Approach to {topic}", "description": "Think outside conventional methods", "feasibility": "medium"},
                {"title": f"Collaborative Solution", "description": "Involve multiple stakeholders", "feasibility": "high"},
                {"title": f"Sustainable Practice", "description": "Focus on long-term sustainability", "feasibility": "high"},
                {"title": f"User-Focused Design", "description": "Prioritize user needs and feedback", "feasibility": "high"},
                {"title": f"Iterative Improvement", "description": "Implement continuous enhancement", "feasibility": "high"}
            ]

def create_content_agent() -> Agent:
    """Create the Content Generation Agent"""
    
    text_generator = TextGeneratorTool()
    email_composer = EmailComposerTool()
    idea_brainstormer = IdeaBrainstormerTool()
    
    content_agent = Agent(
        role="Content Creator",
        goal="Генерувати високоякісний контент, тексти, листи та креативні ідеї відповідно до потреб користувача",
        backstory="""Ти досвідчений контент-креатор та копірайтер з широким досвідом у створенні 
        різноманітного контенту. Твої навички охоплюють:
        
        - Професійне написання листів та документів
        - Креативне письмо та сторітелінг  
        - Ділову комунікацію та презентації
        - Генерацію ідей та брейнсторминг
        - Адаптацію тону та стилю під аудиторію
        
        Ти розумієш важливість ясності, переконливості та відповідності контенту 
        цілям та аудиторії. Завжди враховуєш контекст та специфічні вимоги.""",
        tools=[text_generator, email_composer, idea_brainstormer],
        verbose=True,
        memory=True,
        max_iter=3,
        max_execution_time=30
    )
    
    return content_agent

class ContentService:
    """Service class for managing content generation operations"""
    
    def __init__(self):
        self.content_agent = create_content_agent()
        logger.info("Content Agent initialized successfully")
    
    async def generate_text(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text content"""
        try:
            text_generator = TextGeneratorTool()
            result = text_generator._run(generation_request)
            
            return {
                "success": result.get("generated", False),
                "content": result.get("content", ""),
                "word_count": result.get("word_count", 0),
                "character_count": result.get("character_count", 0),
                "type": result.get("type", "general"),
                "tone": result.get("tone", "professional"),
                "message": result.get("message", "Text generation failed")
            }
            
        except Exception as e:
            logger.error(f"Error in generate_text: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate text content"
            }
    
    async def compose_email(self, email_request: Dict[str, Any]) -> Dict[str, Any]:
        """Compose an email"""
        try:
            email_composer = EmailComposerTool()
            result = email_composer._run(email_request)
            
            return {
                "success": result.get("composed", False),
                "email_content": result.get("email_content", ""),
                "subject": result.get("subject", ""),
                "recipient": result.get("recipient", ""),
                "tone": result.get("tone", "professional"),
                "has_attachment": result.get("has_attachment", False),
                "message": result.get("message", "Email composition failed")
            }
            
        except Exception as e:
            logger.error(f"Error in compose_email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to compose email"
            }
    
    async def brainstorm_ideas(self, brainstorm_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brainstorming ideas"""
        try:
            idea_brainstormer = IdeaBrainstormerTool()
            result = idea_brainstormer._run(brainstorm_request)
            
            return {
                "success": result.get("brainstormed", False),
                "topic": result.get("topic", ""),
                "ideas": result.get("ideas", []),
                "idea_count": result.get("idea_count", 0),
                "focus_area": result.get("focus_area", "general"),
                "message": result.get("message", "Brainstorming failed")
            }
            
        except Exception as e:
            logger.error(f"Error in brainstorm_ideas: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate ideas"
            }
    
    async def process_content_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process general content generation requests"""
        try:
            # Analyze the request
            analysis = self._analyze_content_request(user_message)
            
            # Generate appropriate content based on analysis
            if analysis["intent"] == "generate_email":
                email_request = self._extract_email_details(user_message, analysis)
                return await self.compose_email(email_request)
            elif analysis["intent"] == "generate_text":
                text_request = self._extract_text_details(user_message, analysis)
                return await self.generate_text(text_request)
            elif analysis["intent"] == "brainstorm":
                brainstorm_request = self._extract_brainstorm_details(user_message, analysis)
                return await self.brainstorm_ideas(brainstorm_request)
            else:
                return {
                    "success": True,
                    "analysis": analysis,
                    "recommendations": self._generate_content_recommendations(analysis),
                    "next_actions": self._suggest_content_actions(analysis)
                }
                
        except Exception as e:
            logger.error(f"Error processing content request: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process content request"
            }
    
    def _analyze_content_request(self, user_message: str) -> Dict[str, Any]:
        """Analyze user message for content generation intent"""
        message_lower = user_message.lower()
        
        analysis = {
            "intent": "general",
            "confidence": 0.5,
            "content_type": "text",
            "tone": "professional",
            "extracted_entities": {}
        }
        
        # Detect intent
        if any(word in message_lower for word in ['email', 'write email', 'compose', 'send']):
            analysis["intent"] = "generate_email"
            analysis["confidence"] = 0.9
            analysis["content_type"] = "email"
        elif any(word in message_lower for word in ['write', 'create', 'generate', 'draft']):
            analysis["intent"] = "generate_text"
            analysis["confidence"] = 0.8
        elif any(word in message_lower for word in ['ideas', 'brainstorm', 'think of', 'suggest']):
            analysis["intent"] = "brainstorm"
            analysis["confidence"] = 0.9
        
        # Detect tone
        if any(word in message_lower for word in ['formal', 'professional', 'business']):
            analysis["tone"] = "formal"
        elif any(word in message_lower for word in ['casual', 'informal', 'friendly']):
            analysis["tone"] = "casual"
        elif any(word in message_lower for word in ['creative', 'fun', 'engaging']):
            analysis["tone"] = "creative"
        
        return analysis
    
    def _extract_email_details(self, user_message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract email details from user message"""
        return {
            "recipient": self._extract_recipient(user_message),
            "subject": self._extract_subject(user_message),
            "purpose": user_message,
            "tone": analysis.get("tone", "professional"),
            "include_attachment": "attach" in user_message.lower()
        }
    
    def _extract_text_details(self, user_message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text generation details"""
        return {
            "type": self._determine_text_type(user_message),
            "prompt": user_message,
            "tone": analysis.get("tone", "professional"),
            "length": self._determine_length(user_message)
        }
    
    def _extract_brainstorm_details(self, user_message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract brainstorming details"""
        return {
            "topic": self._extract_topic(user_message),
            "quantity": self._extract_quantity(user_message),
            "focus_area": self._determine_focus_area(user_message)
        }
    
    def _extract_recipient(self, message: str) -> str:
        """Extract recipient from message"""
        # Simple extraction - could be enhanced with NLP
        if "to " in message.lower():
            parts = message.lower().split("to ")
            if len(parts) > 1:
                recipient_part = parts[1].split()[0]
                return recipient_part.title()
        return "Recipient"
    
    def _extract_subject(self, message: str) -> str:
        """Extract subject from message"""
        if "about " in message.lower():
            parts = message.lower().split("about ")
            if len(parts) > 1:
                return parts[1].split('.')[0].title()
        return "Email Subject"
    
    def _determine_text_type(self, message: str) -> str:
        """Determine text type from message"""
        message_lower = message.lower()
        if "letter" in message_lower:
            return "letter"
        elif "summary" in message_lower:
            return "summary"
        elif "business" in message_lower:
            return "business"
        elif "creative" in message_lower:
            return "creative"
        return "general"
    
    def _determine_length(self, message: str) -> str:
        """Determine desired length from message"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['short', 'brief', 'quick']):
            return "short"
        elif any(word in message_lower for word in ['long', 'detailed', 'comprehensive']):
            return "long"
        return "medium"
    
    def _extract_topic(self, message: str) -> str:
        """Extract topic for brainstorming"""
        # Remove brainstorming keywords to get the topic
        cleaned = re.sub(r'\b(ideas?|brainstorm|think of|suggest)\b', '', message.lower()).strip()
        return cleaned if cleaned else "general topic"
    
    def _extract_quantity(self, message: str) -> int:
        """Extract desired number of ideas"""
        numbers = re.findall(r'\d+', message)
        if numbers:
            return min(int(numbers[0]), 10)  # Cap at 10 ideas
        return 5  # Default
    
    def _determine_focus_area(self, message: str) -> str:
        """Determine focus area for brainstorming"""
        message_lower = message.lower()
        if any(word in message_lower for word in ['business', 'marketing', 'strategy']):
            return "business"
        elif any(word in message_lower for word in ['creative', 'design', 'art']):
            return "creative"
        elif any(word in message_lower for word in ['technical', 'tech', 'development']):
            return "technical"
        return "general"
    
    def _generate_content_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        intent = analysis.get("intent", "general")
        
        if intent == "generate_email":
            return [
                "I can help you compose professional emails",
                "Specify the recipient and subject for better results",
                "Let me know the tone (formal, casual, friendly)"
            ]
        elif intent == "generate_text":
            return [
                "I can create various types of text content",
                "Specify the type (letter, summary, creative, business)",
                "Include desired length and tone preferences"
            ]
        elif intent == "brainstorm":
            return [
                "I can generate creative ideas for your topic",
                "Specify focus area (business, creative, technical)",
                "Let me know how many ideas you'd like"
            ]
        else:
            return [
                "I can help with emails, text generation, and brainstorming",
                "Try asking me to 'write an email', 'create content', or 'brainstorm ideas'"
            ]
    
    def _suggest_content_actions(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest next actions based on analysis"""
        intent = analysis.get("intent", "general")
        
        if intent == "generate_email":
            return ["collect_email_details", "compose_email"]
        elif intent == "generate_text":
            return ["collect_text_specifications", "generate_content"]
        elif intent == "brainstorm":
            return ["collect_brainstorm_criteria", "generate_ideas"]
        else:
            return ["clarify_content_intent", "provide_content_help"] 