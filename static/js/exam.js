// Main exam functionality with peer connections and proctoring
(() => {
  "use strict";

  // ------------------ Config ------------------
  const backendURL = window.location.origin;
  const FRAME_INTERVAL_MS = 1000;      
  const VIOLATION_COOLDOWN_MS = 3000;
  const PEER_HOST = "0.peerjs.com";
  const PEER_PORT = 443;
  const PEER_SECURE = true;

  // ------------------ Elements ------------------
  const webcam = document.getElementById("webcam");
  const frameCanvas = document.createElement("canvas");
  frameCanvas.width = 640;
  frameCanvas.height = 480;
  frameCanvas.style.display = "none";
  document.body.appendChild(frameCanvas);
  const canvasCtx = frameCanvas.getContext("2d");
  const focusWarning = document.getElementById("focusWarning");
  const violationDisplay = document.getElementById("violationDisplay");

  // ------------------ State ------------------
  let localStream = null;
  let studentPeerId = null;
  let pendingCall = null;
  let frameIntervalHandle = null;
  let lastFrameSentAt = 0;
  let lastViolationSent = new Map();
  let peer = null;
  let violationCount = 0;
  let proctorConnections = new Map(); // Track proctor connections
  let connectionAttempts = new Map(); // Track connection attempts

  // Connection state management
  function saveStudentState() {
    const state = {
      peerId: studentPeerId,
      proctorConnections: Array.from(proctorConnections.keys()),
      timestamp: Date.now()
    };
    safeSetLocal('studentConnectionState', JSON.stringify(state));
  }

  function loadStudentState() {
    try {
      const saved = safeGetLocal('studentConnectionState');
      if (saved) {
        const state = JSON.parse(saved);
        // Only restore if less than 5 minutes old
        if (Date.now() - state.timestamp < 300000) {
          return state;
        }
      }
    } catch (e) { console.warn('Failed to load student state:', e); }
    return null;
  }

  // ------------------ Utilities ------------------
  function safeSetLocal(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }
  function safeGetLocal(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ------------------ PeerJS Setup ------------------
  function initializePeer() {
    if (peer && !peer.destroyed) {
      peer.destroy();
    }
    
    peer = new Peer({
      host: PEER_HOST,
      port: PEER_PORT,
      secure: PEER_SECURE
    });

    peer.on("open", (id) => {
      console.log("🆔 Student Peer ID:", id);
      studentPeerId = id;
      safeSetLocal("exam_peer_id", id);
      
      // Update hidden form field
      const peerIdField = document.getElementById("peer-id-field");
      if (peerIdField) peerIdField.value = id;
      
      // Restore previous state if available
      const savedState = loadStudentState();
      if (savedState && savedState.peerId === id) {
        console.log('🔄 Restoring student connection state');
        savedState.proctorConnections.forEach(proctorId => {
          connectionAttempts.set(proctorId, 0);
        });
      }
      
      sendPeerIdToServer(id);
      saveStudentState();
    });

    peer.on("call", (call) => {
      console.log("📞 Incoming call from proctor:", call.peer);
      
      // Store the connection
      proctorConnections.set(call.peer, call);
      
      if (localStream) {
        console.log("✅ Answering call with stream");
        call.answer(localStream);
      } else {
        console.log("⚠️ No stream available, storing call");
        pendingCall = call;
      }
      
      call.on("error", (err) => {
        console.error("❌ Call error:", err);
        proctorConnections.delete(call.peer);
        saveStudentState();
      });
      
      call.on("close", () => {
        console.log("📞 Call closed by proctor");
        proctorConnections.delete(call.peer);
        saveStudentState();
      });
      
      saveStudentState();
    });
  }

  function connectToProctor() {
    if (!localStream || !peer || peer.destroyed) {
      console.warn("⚠️ Not ready for proctor connection");
      return;
    }
    
    console.log("🔍 Looking for proctors...");
    
    fetch(`${backendURL}/get-proctor-ids`)
      .then(res => res.json())
      .then(proctorIds => {
        console.log("📋 Found proctors:", proctorIds);
        
        proctorIds.forEach(proctorId => {
          if (proctorId !== studentPeerId) {
            // Check if already connected or recently attempted
            const attempts = connectionAttempts.get(proctorId) || 0;
            if (!proctorConnections.has(proctorId) && attempts < 3) {
              console.log("📞 Calling proctor:", proctorId);
              connectionAttempts.set(proctorId, attempts + 1);
              
              try {
                const call = peer.call(proctorId, localStream);
                
                if (call) {
                  console.log("✅ Call created successfully to:", proctorId);
                  proctorConnections.set(proctorId, call);
                  
                  call.on("error", (err) => {
                    console.error("❌ Call to proctor failed:", proctorId, err);
                    proctorConnections.delete(proctorId);
                  });
                  
                  call.on("close", () => {
                    console.log("📞 Call to proctor closed:", proctorId);
                    proctorConnections.delete(proctorId);
                  });
                  
                  saveStudentState();
                }
              } catch (error) {
                console.error("❌ Exception calling proctor:", proctorId, error);
              }
            }
          }
        });
      })
      .catch(err => {
        console.error("❌ Failed to get proctor IDs:", err);
      });
  }

  function sendPeerIdToServer(peerId) {
    if (!peerId) return;
    
    const studentEmail = getStudentEmail();
    const studentName = getStudentName();
    
    fetch(`${backendURL}/store-peer-id`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        peerId, 
        email: studentEmail,
        name: studentName
      })
    }).catch(err => console.error("Failed to send peer ID:", err));
  }
  
  function getStudentEmail() {
    // Use actual login email from session
    return window.studentInfo?.email || 
           sessionStorage.getItem('student_email') || 
           new URLSearchParams(window.location.search).get('email') || 
           'unknown@student.com';
  }
  
  function getStudentName() {
    // Use actual name from session
    return window.studentInfo?.name || 
           sessionStorage.getItem('student_name') || 
           new URLSearchParams(window.location.search).get('name') || 
           'Student';
  }

  // ------------------ Camera & Proctoring ------------------
  async function initializeCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      localStream = stream;
      
      // Create hidden webcam element if it doesn't exist
      let webcamElement = document.getElementById("webcam");
      if (!webcamElement) {
        webcamElement = document.createElement("video");
        webcamElement.id = "webcam";
        webcamElement.autoplay = true;
        webcamElement.playsinline = true;
        webcamElement.muted = true;
        webcamElement.style.visibility = "hidden";
        webcamElement.style.width = "0";
        webcamElement.style.height = "0";
        document.body.appendChild(webcamElement);
      }
      
      webcamElement.srcObject = stream;

      if (pendingCall) {
        pendingCall.answer(localStream);
        pendingCall = null;
      }

      // Connect to proctor
      setTimeout(() => {
        connectToProctor();
        // Set up periodic proctor detection
        setInterval(connectToProctor, 10000); // Check every 10 seconds
      }, 2000);

      // Start frame capture for proctoring
      startFrameCapture();

      console.log("✅ Camera and proctoring initialized");
    } catch (err) {
      console.error("❌ Camera access failed:", err);
      alert("Camera access is required for the exam. Please allow permission and refresh.");
    }
  }

  function startFrameCapture() {
    if (!canvasCtx) return;

    if (frameIntervalHandle) clearInterval(frameIntervalHandle);

    frameIntervalHandle = setInterval(() => {
      if (!localStream || document.hidden || !document.hasFocus()) return;

      const webcamElement = document.getElementById("webcam");
      if (!webcamElement) return;

      if (webcamElement.videoWidth && webcamElement.videoHeight) {
        frameCanvas.width = webcamElement.videoWidth;
        frameCanvas.height = webcamElement.videoHeight;
      }

      try {
        canvasCtx.drawImage(webcamElement, 0, 0, frameCanvas.width, frameCanvas.height);
        const now = Date.now();
        if (now - lastFrameSentAt < FRAME_INTERVAL_MS) return;
        lastFrameSentAt = now;

        // Pipeline 0: Frame Transport Only
        const imageData = frameCanvas.toDataURL("image/jpeg", 0.8); // Use JPEG for efficiency
        const payload = {
          image: imageData,
          peerId: studentPeerId || safeGetLocal("exam_peer_id")
        };

        // Fire-and-forget request to Pipeline 0
        fetch(`${backendURL}/pipeline0/frame`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
        .catch(err => {
          console.error("Pipeline 0 frame transport error:", err);
        });
        // Note: Ignoring response as per Pipeline 0 requirements
        
      } catch (e) {
        console.error("Frame capture error:", e);
      }
    }, FRAME_INTERVAL_MS);
  }

  // Note: Violation handling removed for Pipeline 0
  // These functions kept for tab detection and other exam protection
  function endExamDueToViolations() {
    cleanupAndExit("Exam terminated due to repeated violations.");
  }

  function cleanupAndExit(message) {
    try {
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
      }
      if (webcam) webcam.srcObject = null;
      if (peer && !peer.destroyed) {
        peer.destroy();
      }
    } catch (e) { console.warn(e); }

    const peerIdToDelete = studentPeerId || safeGetLocal("exam_peer_id");
    const studentEmail = getStudentEmail();
    
    if (peerIdToDelete) {
      fetch(`${backendURL}/delete-peer-id`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          peerId: peerIdToDelete, 
          type: "student",
          email: studentEmail
        })
      }).catch(e => console.warn("Cleanup error:", e));
    }

    safeSetLocal("exam_active", "0");
    safeSetLocal("exam_peer_id", "");
    alert(message);
    window.location.href = "/";
  }

  // ------------------ Violation Display Functions ------------------
  function showViolationPopup(reasons, count) {
    const reasonText = reasons.join(", ");
    const message = `⚠️ VIOLATION DETECTED!\n\nReason: ${reasonText}\nTotal Violations: ${count}/5\n\n${count >= 5 ? 'EXAM WILL BE TERMINATED!' : 'Please maintain exam integrity.'}`;
    
    // Use SweetAlert2 if available, otherwise use regular alert
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'warning',
        title: 'Violation Detected!',
        text: `${reasonText}\nTotal Violations: ${count}/5`,
        confirmButtonText: 'I Understand',
        allowOutsideClick: false,
        timer: count >= 5 ? undefined : 5000
      });
    } else {
      alert(message);
    }
  }

  function updateViolationDisplay(reasons, count) {
    if (violationDisplay) {
      violationDisplay.style.display = "block";
      violationDisplay.innerHTML = `
        <div style="background: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 15px; margin: 10px 0;">
          <strong style="color: #d32f2f;">⚠️ Violations: ${count}/5</strong><br>
          <span style="color: #666;">Latest: ${reasons.join(", ")}</span>
        </div>
      `;
    }
  }

  // ------------------ Exam Protection ------------------
  function enableExamProtection() {
    // Fullscreen enforcement
    document.addEventListener("fullscreenchange", () => {
      if (!document.fullscreenElement) {
        // sendTabViolation("Exited fullscreen");
        try { document.documentElement.requestFullscreen().catch(()=>{}); } catch(e){}
      }
    });

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        // sendTabViolation("Page hidden or switched tab");
        try { document.title = "⚠ RETURN TO EXAM"; } catch(e){}
      } else {
        try { document.title = "Student Exam"; } catch(e){}
        try { document.documentElement.requestFullscreen().catch(()=>{}); } catch(e){}
        try { window.focus(); } catch(e){}
      }
    });

    window.addEventListener("blur", () => {
      // sendTabViolation("Window lost focus (possible alt+tab)");
    });

    // Prevent shortcuts
    window.addEventListener("keydown", function (e) {
      const blocked =
        e.key === "F11" ||
        e.key === "F12" ||
        (e.ctrlKey && (e.key === "t" || e.key === "w" || e.key === "Tab" || e.key === "r")) ||
        (e.metaKey && (e.key === "t" || e.key === "w")) ||
        (e.ctrlKey && e.shiftKey && (e.key === "I" || e.key === "i")) ||
        (e.ctrlKey && e.shiftKey && e.key === "C");

      if (blocked) {
        e.preventDefault?.();
        e.stopPropagation?.();
        // sendTabViolation(`Blocked shortcut attempt: ${e.key}`);
        return false;
      }
    }, true);

    // Prevent page exit
    window.addEventListener("beforeunload", (e) => {
      const active = safeGetLocal("exam_active");
      if (active === "1") {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    });
  }

  // function sendTabViolation(reason) {
  //   if (!reason) return;

  //   const now = Date.now();
  //   const last = lastViolationSent.get(reason) || 0;
  //   if (now - last < VIOLATION_COOLDOWN_MS) return;
  //   lastViolationSent.set(reason, now);

  //   const peerId = studentPeerId || safeGetLocal("exam_peer_id") || null;
  //   fetch(`${backendURL}/tab-violation`, {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ peerId, reason })
  //   })
  //   .then(res => res.json().catch(() => ({})))
  //   .then(data => {
  //     console.log("Tab violation logged:", reason, data);
  //     violationCount = data.count || violationCount + 1;
  //     showViolationPopup([reason], violationCount);
  //     updateViolationDisplay([reason], violationCount);
  //     if (focusWarning) {
  //       focusWarning.style.display = "block";
  //       focusWarning.textContent = `⚠️ ${reason} — Violations: ${violationCount}`;
  //     }
  //     if (data.action === "stop_exam") {
  //       endExamDueToViolations();
  //     }
  //   })
  //   .catch(err => console.error("Tab violation send error:", err));
  // }

  // Add visibility change handler to reconnect when page becomes visible
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden && localStream && peer && !peer.destroyed) {
      console.log('📱 Page visible, checking proctor connections...');
      setTimeout(connectToProctor, 1000);
    }
  });

  // ------------------ Cleanup ------------------
  window.addEventListener("unload", () => {
    try {
      const peerIdToDelete = studentPeerId || safeGetLocal("exam_peer_id");
      if (peerIdToDelete) {
        const data = JSON.stringify({ peerId: peerIdToDelete, type: "student" });
        if (navigator.sendBeacon) {
          navigator.sendBeacon(`${backendURL}/delete-peer-id`, data);
        }
      }
      safeSetLocal("exam_peer_id", "");
      safeSetLocal("exam_active", "0");
    } catch (e) {}
  });

  // ------------------ Initialize Everything ------------------
  document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Initializing exam...");
    
    // Initialize quiz navigation
    initializeQuizNavigation();
    
    // Mark exam as active
    safeSetLocal("exam_active", "1");
    
    // Initialize peer connection
    initializePeer();
    
    // Initialize camera and proctoring
    initializeCamera();
    
    // Enable exam protection
    enableExamProtection();
    
    // Force fullscreen
    try {
      document.documentElement.requestFullscreen().catch(()=>{});
    } catch(e){}
  });

  // ------------------ Quiz Navigation Logic ------------------
  function initializeQuizNavigation() {
    const questions = document.querySelectorAll('.question-block');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const currentQuestionSpan = document.getElementById('current-question');
    const totalQuestionsSpan = document.getElementById('total-questions');
    const progressBar = document.querySelector('.progress-bar');
    
    let currentQuestion = 0;
    const totalQuestions = questions.length;
    
    if (totalQuestionsSpan) totalQuestionsSpan.textContent = totalQuestions;
    
    function showQuestion(index) {
      questions.forEach((q, i) => {
        q.classList.toggle('active', i === index);
      });
      
      if (currentQuestionSpan) currentQuestionSpan.textContent = index + 1;
      if (progressBar) {
        const progress = ((index + 1) / totalQuestions) * 100;
        progressBar.style.width = progress + '%';
      }
      
      // Update exam session progress
      if (typeof updateExamProgress === 'function') {
        updateExamProgress(index + 1);
      }
      
      // Update button visibility
      if (prevBtn) prevBtn.style.display = index === 0 ? 'none' : 'inline-block';
      if (nextBtn) nextBtn.style.display = index === totalQuestions - 1 ? 'none' : 'inline-block';
      if (submitBtn) submitBtn.style.display = index === totalQuestions - 1 ? 'inline-block' : 'none';
    }
    
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentQuestion > 0) {
          currentQuestion--;
          showQuestion(currentQuestion);
        }
      });
    }
    
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (currentQuestion < totalQuestions - 1) {
          currentQuestion++;
          showQuestion(currentQuestion);
        }
      });
    }
    
    if (submitBtn) {
      submitBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to submit your exam?')) {
          cleanupAndExit("Exam submitted successfully!");
          // Allow form submission after cleanup
          setTimeout(() => {
            document.getElementById('quiz-form').submit();
          }, 100);
        }
      });
    }
    
    // Initialize first question
    if (totalQuestions > 0) {
      showQuestion(0);
    }
  }

})();