"""Analytics for user performance."""
from typing import List, Dict, Any
from backend.quiz_service.models.user_state import UserPerformance


class PerformanceAnalytics:
    """Analyze user performance and generate insights."""
    
    @staticmethod
    def get_topic_breakdown(performance: UserPerformance) -> List[Dict[str, Any]]:
        """Get performance breakdown by topic.
        
        Args:
            performance: UserPerformance instance
            
        Returns:
            List of topic performance dictionaries
        """
        breakdown = []
        
        for topic_name, topic_score in performance.topic_scores.items():
            total_attempts = sum(
                cs.attempts 
                for ss in topic_score.subtopic_scores.values() 
                for cs in ss.concept_scores.values()
            )
            
            total_correct = sum(
                cs.correct 
                for ss in topic_score.subtopic_scores.values() 
                for cs in ss.concept_scores.values()
            )
            
            breakdown.append({
                "topic": topic_name,
                "attempts": total_attempts,
                "correct": total_correct,
                "accuracy": topic_score.overall_accuracy,
                "subtopic_count": len(topic_score.subtopic_scores)
            })
        
        # Sort by accuracy (lowest first) to highlight weak areas
        breakdown.sort(key=lambda x: x["accuracy"])
        return breakdown
    
    @staticmethod
    def get_concept_priorities(performance: UserPerformance) -> List[tuple[str, str, str, float]]:
        """Get prioritized list of concepts to study.
        
        Args:
            performance: UserPerformance instance
            
        Returns:
            List of (topic, subtopic, concept, priority_score) tuples
            Priority score: lower = higher priority
        """
        priorities = []
        
        for topic_name, topic_score in performance.topic_scores.items():
            for subtopic_name, subtopic_score in topic_score.subtopic_scores.items():
                for concept_name, concept_score in subtopic_score.concept_scores.items():
                    # Calculate priority score
                    # Lower score = higher priority
                    if concept_score.attempts == 0:
                        priority = 1000  # Untried concepts have low priority
                    else:
                        # Weak concepts (low accuracy) get high priority (low score)
                        # Recency also matters - recently attempted get lower priority
                        accuracy_factor = concept_score.accuracy / 100.0  # 0-1
                        attempts_factor = min(concept_score.attempts / 5.0, 1.0)  # 0-1
                        
                        # Priority = accuracy weighted by attempts
                        # Low accuracy + multiple attempts = high priority (low score)
                        priority = accuracy_factor * (1 + attempts_factor)
                    
                    priorities.append((topic_name, subtopic_name, concept_name, priority))
        
        # Sort by priority (lowest first = highest priority)
        priorities.sort(key=lambda x: x[3])
        return priorities
    
    @staticmethod
    def get_mastery_level(performance: UserPerformance) -> str:
        """Determine overall mastery level.
        
        Args:
            performance: UserPerformance instance
            
        Returns:
            Mastery level string
        """
        accuracy = performance.overall_accuracy
        attempts = performance.total_questions_answered
        
        if attempts < 5:
            return "Beginner"
        elif attempts < 15:
            if accuracy >= 75:
                return "Intermediate"
            else:
                return "Beginner"
        else:
            if accuracy >= 85:
                return "Advanced"
            elif accuracy >= 70:
                return "Intermediate"
            else:
                return "Beginner"
    
    @staticmethod
    def generate_insights(performance: UserPerformance) -> List[str]:
        """Generate human-readable insights.
        
        Args:
            performance: UserPerformance instance
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Overall performance
        if performance.total_questions_answered == 0:
            insights.append("Start answering questions to see your progress!")
            return insights
        
        accuracy = performance.overall_accuracy
        if accuracy >= 80:
            insights.append(f"Excellent work! You're at {accuracy:.1f}% accuracy.")
        elif accuracy >= 60:
            insights.append(f"Good progress! You're at {accuracy:.1f}% accuracy.")
        else:
            insights.append(f"Keep practicing! You're at {accuracy:.1f}% accuracy.")
        
        # Weak areas
        weak_concepts = performance.get_all_weak_concepts()
        if weak_concepts:
            insights.append(f"You have {len(weak_concepts)} concepts that need more practice.")
        
        # Topic breakdown
        topic_breakdown = PerformanceAnalytics.get_topic_breakdown(performance)
        if topic_breakdown:
            weakest_topic = topic_breakdown[0]
            if weakest_topic["attempts"] > 0:
                insights.append(
                    f"Focus on '{weakest_topic['topic']}' "
                    f"(currently at {weakest_topic['accuracy']:.1f}%)."
                )
        
        # Mastery level
        mastery = PerformanceAnalytics.get_mastery_level(performance)
        insights.append(f"Your current level: {mastery}")
        
        return insights

