// Exam Session Management
class ExamSessionManager {
    constructor() {
        this.sessionId = null;
        this.status = 'inactive';
        this.checkInterval = null;
        this.init();
    }

    async init() {
        // Start or resume exam session
        if (window.examSession) {
            this.sessionId = window.examSession.id;
            this.status = window.examSession.status;
            console.log('Resuming exam session:', this.sessionId, 'Status:', this.status);
        } else {
            await this.startExamSession();
        }
        
        this.startStatusChecking();
        this.handleExamStatus();
    }

    async startExamSession() {
        try {
            const response = await fetch('/api/exam/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.status = data.status;
                console.log('Started exam session:', this.sessionId);
            }
        } catch (error) {
            console.error('Error starting exam session:', error);
        }
    }

    startStatusChecking() {
        // Check exam status every 3 seconds
        this.checkInterval = setInterval(() => {
            this.checkExamStatus();
        }, 3000);
    }

    async checkExamStatus() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/exam/status/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.status !== this.status) {
                    this.status = data.status;
                    this.handleExamStatus();
                }
            }
        } catch (error) {
            console.error('Error checking exam status:', error);
        }
    }

    handleExamStatus() {
        const examContainer = document.querySelector('.quiz-wrapper');
        const statusOverlay = document.getElementById('statusOverlay') || this.createStatusOverlay();
        
        switch (this.status) {
            case 'active':
                statusOverlay.style.display = 'none';
                examContainer.style.pointerEvents = 'auto';
                examContainer.style.opacity = '1';
                break;
                
            case 'paused':
                statusOverlay.innerHTML = `
                    <div class="status-message paused">
                        <i class="fas fa-pause-circle"></i>
                        <h2>Exam Paused</h2>
                        <p>Your exam has been paused by the administrator.</p>
                        <p>Please wait for further instructions.</p>
                    </div>
                `;
                statusOverlay.style.display = 'flex';
                examContainer.style.pointerEvents = 'none';
                examContainer.style.opacity = '0.5';
                break;
                
            case 'ended':
                statusOverlay.innerHTML = `
                    <div class="status-message ended">
                        <i class="fas fa-stop-circle"></i>
                        <h2>Exam Ended</h2>
                        <p>Your exam has been ended by the administrator.</p>
                        <button onclick="window.location.href='/student_dashboard'" class="btn-return">
                            Return to Dashboard
                        </button>
                    </div>
                `;
                statusOverlay.style.display = 'flex';
                examContainer.style.pointerEvents = 'none';
                this.stopStatusChecking();
                break;
        }
    }

    createStatusOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'statusOverlay';
        overlay.innerHTML = '';
        document.body.appendChild(overlay);
        return overlay;
    }

    async updateProgress(currentQuestion) {
        if (!this.sessionId) return;
        
        try {
            await fetch('/api/exam/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    current_question: currentQuestion
                })
            });
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }

    stopStatusChecking() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
}

// Initialize exam session manager when page loads
let examSessionManager;
document.addEventListener('DOMContentLoaded', () => {
    examSessionManager = new ExamSessionManager();
});

// Update progress when question changes
function updateExamProgress(questionNumber) {
    if (examSessionManager) {
        examSessionManager.updateProgress(questionNumber);
    }
}