from datetime import datetime
from enum import Enum

class ViolationType(Enum):
    ABSENCE = "absence"
    MULTIPLE_PERSONS = "multiple_persons"
    UNAUTHORIZED_MATERIALS = "unauthorized_materials"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    TECHNICAL_ISSUE = "technical_issue"

class SeverityLevel(Enum):
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EnhancedViolationAnalyzer:
    def __init__(self):
        # Violation scoring weights
        self.violation_weights = {
            ViolationType.ABSENCE: 40,
            ViolationType.MULTIPLE_PERSONS: 60,
            ViolationType.UNAUTHORIZED_MATERIALS: 70,
            ViolationType.SUSPICIOUS_BEHAVIOR: 30,
            ViolationType.TECHNICAL_ISSUE: 20
        }
        
        # Object risk categories
        self.high_risk_objects = {
            'phone', 'mobile phone', 'cell phone', 'smartphone',
            'book', 'notebook', 'paper', 'document', 'notes'
        }
        
        self.medium_risk_objects = {
            'computer', 'laptop', 'tablet', 'monitor', 'screen',
            'watch', 'smartwatch', 'calculator'
        }
        
        self.low_risk_objects = {
            'person', 'people', 'human', 'chair', 'desk', 'table'
        }

    def analyze_comprehensive_violation(self, detection_results):
        """
        Comprehensive violation analysis based on detection results
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'violations': [],
            'total_score': 0,
            'severity': SeverityLevel.MINIMAL,
            'is_violation': False,
            'recommendations': [],
            'detailed_analysis': {}
        }
        
        # Analyze local detection results
        local_results = detection_results.get('local_detection', {})
        azure_results = detection_results.get('azure_detection', {})
        
        # Face analysis
        face_violations = self._analyze_face_violations(local_results, azure_results)
        analysis['violations'].extend(face_violations)
        
        # Object analysis (from Azure CV)
        if azure_results and 'objects' in azure_results:
            object_violations = self._analyze_object_violations(azure_results['objects'])
            analysis['violations'].extend(object_violations)
        
        # Behavioral analysis (from Azure suspicion analysis)
        if azure_results and 'suspicion_analysis' in azure_results:
            behavior_violations = self._analyze_behavioral_violations(azure_results['suspicion_analysis'])
            analysis['violations'].extend(behavior_violations)
        
        # Calculate total score and severity
        analysis['total_score'] = sum(v['score'] for v in analysis['violations'])
        analysis['severity'] = self._calculate_severity(analysis['total_score'])
        analysis['is_violation'] = analysis['total_score'] >= 50
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis['violations'])
        
        # Detailed breakdown
        analysis['detailed_analysis'] = self._create_detailed_analysis(analysis['violations'])
        
        return analysis
    
    def _analyze_face_violations(self, local_results, azure_results):
        """Analyze face-related violations"""
        violations = []
        
        # Prioritize Azure face count if available
        local_face_count = local_results.get('face_count', 0)
        azure_face_count = azure_results.get('face_count', 0) if azure_results else 0
        
        face_count = azure_face_count if azure_face_count > 0 else local_face_count
        
        if face_count == 0:
            violations.append({
                'type': ViolationType.ABSENCE,
                'description': 'No face detected - student may not be present',
                'score': self.violation_weights[ViolationType.ABSENCE],
                'confidence': 0.9,
                'evidence': f'Face detection count: {face_count}'
            })
        elif face_count > 1:
            violations.append({
                'type': ViolationType.MULTIPLE_PERSONS,
                'description': f'Multiple faces detected ({face_count}) - unauthorized assistance',
                'score': self.violation_weights[ViolationType.MULTIPLE_PERSONS],
                'confidence': 0.85,
                'evidence': f'Face detection count: {face_count}'
            })
        
        return violations
    
    def _analyze_object_violations(self, detected_objects):
        """Analyze object-related violations"""
        violations = []
        
        high_risk_found = []
        medium_risk_found = []
        
        for obj in detected_objects:
            obj_name = obj['name'].lower()
            confidence = obj['confidence']
            
            if confidence > 0.6:  # High confidence threshold
                if any(risk in obj_name for risk in self.high_risk_objects):
                    high_risk_found.append(f"{obj_name} ({confidence:.1%})")
                elif any(risk in obj_name for risk in self.medium_risk_objects):
                    medium_risk_found.append(f"{obj_name} ({confidence:.1%})")
        
        if high_risk_found:
            violations.append({
                'type': ViolationType.UNAUTHORIZED_MATERIALS,
                'description': f'High-risk unauthorized materials detected: {", ".join(high_risk_found)}',
                'score': self.violation_weights[ViolationType.UNAUTHORIZED_MATERIALS],
                'confidence': 0.9,
                'evidence': f'Objects: {high_risk_found}'
            })
        
        if medium_risk_found:
            violations.append({
                'type': ViolationType.SUSPICIOUS_BEHAVIOR,
                'description': f'Potentially suspicious objects detected: {", ".join(medium_risk_found)}',
                'score': self.violation_weights[ViolationType.SUSPICIOUS_BEHAVIOR],
                'confidence': 0.7,
                'evidence': f'Objects: {medium_risk_found}'
            })
        
        return violations
    
    def _analyze_behavioral_violations(self, suspicion_analysis):
        """Analyze behavioral violations from Azure analysis"""
        violations = []
        
        if suspicion_analysis.get('is_suspicious', False):
            reasons = suspicion_analysis.get('reasons', [])
            score = suspicion_analysis.get('suspicion_score', 0)
            
            # Filter out face-related reasons (already handled)
            behavioral_reasons = [
                reason for reason in reasons 
                if not any(face_keyword in reason.lower() for face_keyword in ['face', 'faces'])
            ]
            
            if behavioral_reasons:
                violations.append({
                    'type': ViolationType.SUSPICIOUS_BEHAVIOR,
                    'description': 'Suspicious behavioral patterns detected',
                    'score': min(score * 0.5, 40),  # Cap behavioral score
                    'confidence': 0.75,
                    'evidence': behavioral_reasons
                })
        
        return violations
    
    def _calculate_severity(self, total_score):
        """Calculate severity level based on total score"""
        if total_score >= 90:
            return SeverityLevel.CRITICAL
        elif total_score >= 70:
            return SeverityLevel.HIGH
        elif total_score >= 50:
            return SeverityLevel.MEDIUM
        elif total_score >= 30:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.MINIMAL
    
    def _generate_recommendations(self, violations):
        """Generate recommendations based on violations"""
        recommendations = []
        
        violation_types = [v['type'] for v in violations]
        
        if ViolationType.ABSENCE in violation_types:
            recommendations.append("Ensure student is properly positioned in front of camera")
            recommendations.append("Check camera functionality and lighting conditions")
        
        if ViolationType.MULTIPLE_PERSONS in violation_types:
            recommendations.append("Verify only authorized student is present")
            recommendations.append("Investigate potential unauthorized assistance")
        
        if ViolationType.UNAUTHORIZED_MATERIALS in violation_types:
            recommendations.append("Immediate intervention required - unauthorized materials detected")
            recommendations.append("Review exam rules with student")
        
        if ViolationType.SUSPICIOUS_BEHAVIOR in violation_types:
            recommendations.append("Monitor student more closely")
            recommendations.append("Consider additional verification measures")
        
        return recommendations
    
    def _create_detailed_analysis(self, violations):
        """Create detailed analysis breakdown"""
        analysis = {
            'violation_count': len(violations),
            'violation_types': list(set(v['type'].value for v in violations)),
            'highest_score': max([v['score'] for v in violations]) if violations else 0,
            'average_confidence': sum([v['confidence'] for v in violations]) / len(violations) if violations else 0,
            'evidence_summary': []
        }
        
        for violation in violations:
            analysis['evidence_summary'].append({
                'type': violation['type'].value,
                'evidence': violation['evidence'],
                'score': violation['score']
            })
        
        return analysis

def create_enhanced_violation_entry(peer_id, analysis_results):
    """Create enhanced violation entry with comprehensive analysis"""
    analyzer = EnhancedViolationAnalyzer()
    violation_analysis = analyzer.analyze_comprehensive_violation(analysis_results)
    
    if violation_analysis['is_violation']:
        return {
            "peer_id": peer_id,
            "timestamp": violation_analysis['timestamp'],
            "severity": violation_analysis['severity'].value,
            "total_score": violation_analysis['total_score'],
            "violations": [
                {
                    "type": v['type'].value,
                    "description": v['description'],
                    "score": v['score'],
                    "confidence": v['confidence'],
                    "evidence": v['evidence']
                }
                for v in violation_analysis['violations']
            ],
            "recommendations": violation_analysis['recommendations'],
            "detailed_analysis": violation_analysis['detailed_analysis']
        }
    
    return None

# Legacy function for backward compatibility
def create_violation_entry(peer_id, reasons):
    """Legacy function - creates simple violation entry"""
    return {
        "peer_id": peer_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reasons": reasons
    }