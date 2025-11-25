#!/usr/bin/env python3
"""Verify that the application setup is correct."""
import sys
from pathlib import Path

# Add project root to path
BACKEND_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_imports():
    """Test all critical imports."""
    print("🔍 Verifying imports...")
    
    try:
        from backend.course_service.models.course import CourseStructure
        print("  ✅ Models")
    except ImportError as e:
        print(f"  ❌ Models: {e}")
        return False
    
    try:
        from backend.shared.services.llm.mistral_client import MistralClient
        print("  ✅ Mistral client")
    except ImportError as e:
        print(f"  ❌ Mistral client: {e}")
        return False
    
    try:
        from backend.quiz_service.services.question.generator import QuestionGenerator
        print("  ✅ Question generator")
    except ImportError as e:
        print(f"  ❌ Question generator: {e}")
        return False
    
    try:
        from backend.quiz_service.services.tracking.performance_tracker import PerformanceTracker
        print("  ✅ Performance tracker")
    except ImportError as e:
        print(f"  ❌ Performance tracker: {e}")
        return False
    
    try:
        from backend.api.main import app
        print("  ✅ FastAPI app")
    except ImportError as e:
        print(f"  ❌ FastAPI app: {e}")
        return False
    
    return True


def verify_course_material():
    """Check that course material exists."""
    print("\n📚 Verifying course material...")
    
    from pathlib import Path
    course_file = BACKEND_ROOT / "course_service" / "data" / "course_material.json"
    
    if course_file.exists():
        print("  ✅ Course material JSON exists")
        
        try:
            from backend.course_service.services.course_loader import CourseLoader
            course = CourseLoader.load_from_file(str(course_file))
            print(f"  ✅ Course loaded: {course.title}")
            print(f"     Topics: {len(course.topics)}")
            total_concepts = sum(
                len(concept) 
                for topic in course.topics 
                for subtopic in topic.subtopics 
                for concept in [subtopic.concepts]
            )
            print(f"     Total concepts: {total_concepts}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to load course: {e}")
            return False
    else:
        print("  ❌ Course material not found")
        return False


def verify_tests():
    """Check test structure."""
    print("\n🧪 Verifying tests...")
    
    quiz_tests = list((BACKEND_ROOT / "quiz_service" / "tests").glob("test_*.py"))
    course_tests = list((BACKEND_ROOT / "course_service" / "tests").glob("test_*.py"))
    
    print(f"  ✅ Quiz test files: {len(quiz_tests)}")
    print(f"  ✅ Course test files: {len(course_tests)}")
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Adaptive Learning Platform - Setup Verification")
    print("=" * 60)
    
    all_good = True
    
    all_good &= verify_imports()
    all_good &= verify_course_material()
    all_good &= verify_tests()
    
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All checks passed! Ready to run:")
        print("   Backend: cd backend && uv run uvicorn api.main:app --reload --port 8000")
        print("   Frontend: cd frontend && npm install && npm run dev")
        print("   Or use: ./deploy.sh")
    else:
        print("❌ Some checks failed. Please review the errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()

