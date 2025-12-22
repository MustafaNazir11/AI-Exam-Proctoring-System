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
      sendPeerIdToServer(id);
    });

    peer.on("call", (call) => {
      console.log("📞 Incoming call from proctor:", call.peer);
      
      if (localStream) {
        console.log("✅ Answering call with stream");
        call.answer(localStream);
      } else {
        console.log("⚠️ No stream available, storing call");
        pendingCall = call;
      }
      
      call.on("error", (err) => {
        console.error("❌ Call error:", err);
      });
      
      call.on("close", () => {
        console.log("📞 Call closed by proctor");
      });
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
            console.log("📞 Calling proctor:", proctorId);
            
            try {
              const call = peer.call(proctorId, localStream);
              
              if (call) {
                console.log("✅ Call created successfully to:", proctorId);
                
                call.on("error", (err) => {
                  console.error("❌ Call to proctor failed:", proctorId, err);
                });
                
                call.on("close", () => {
                  console.log("📞 Call to proctor closed:", proctorId);
                });
              }
            } catch (error) {
              console.error("❌ Exception calling proctor:", proctorId, error);
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
    fetch(`${backendURL}/store-peer-id`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ peerId })
    }).catch(err => console.error("Failed to send peer ID:", err));
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

        const imageData = frameCanvas.toDataURL("image/png");
        const payload = {
          image: imageData,
          peerId: studentPeerId || safeGetLocal("exam_peer_id")
        };

        fetch(`${backendURL}/upload-screenshot`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
        .then(res => res.json().catch(()=>({})))
        .then(data => {
          if (data.reasons && violationDisplay) {
            violationDisplay.innerHTML = data.reasons.join("<br>");
          }
          if (data.action === "stop_exam") {
            endExamDueToViolations();
          }
        })
        .catch(err => {
          console.error("Frame upload error:", err);
        });
      } catch (e) {
        console.error("Frame capture error:", e);
      }
    }, FRAME_INTERVAL_MS);
  }

  function endExamDueToViolations() {
    try {
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
      }
      if (webcam) webcam.srcObject = null;
    } catch (e) { console.warn(e); }

    safeSetLocal("exam_active", "0");
    alert("Exam terminated due to repeated violations.");
    window.location.href = "/";
  }

  // ------------------ Exam Protection ------------------
  function enableExamProtection() {
    // Fullscreen enforcement
    document.addEventListener("fullscreenchange", () => {
      if (!document.fullscreenElement) {
        sendTabViolation("Exited fullscreen");
        try { document.documentElement.requestFullscreen().catch(()=>{}); } catch(e){}
      }
    });

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        sendTabViolation("Page hidden or switched tab");
        try { document.title = "⚠ RETURN TO EXAM"; } catch(e){}
      } else {
        try { document.title = "Student Exam"; } catch(e){}
        try { document.documentElement.requestFullscreen().catch(()=>{}); } catch(e){}
        try { window.focus(); } catch(e){}
      }
    });

    window.addEventListener("blur", () => {
      sendTabViolation("Window lost focus (possible alt+tab)");
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
        sendTabViolation(`Blocked shortcut attempt: ${e.key}`);
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

  function sendTabViolation(reason) {
    if (!reason) return;

    const now = Date.now();
    const last = lastViolationSent.get(reason) || 0;
    if (now - last < VIOLATION_COOLDOWN_MS) return;
    lastViolationSent.set(reason, now);

    const peerId = studentPeerId || safeGetLocal("exam_peer_id") || null;
    fetch(`${backendURL}/tab-violation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ peerId, reason })
    })
    .then(res => res.json().catch(() => ({})))
    .then(data => {
      console.log("Tab violation logged:", reason, data);
      if (focusWarning) {
        focusWarning.style.display = "block";
        focusWarning.textContent = `⚠️ ${reason} — Violations: ${data.count || "-"}`;
      }
      if (data.action === "stop_exam") {
        endExamDueToViolations();
      }
    })
    .catch(err => console.error("Tab violation send error:", err));
  }

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

})();