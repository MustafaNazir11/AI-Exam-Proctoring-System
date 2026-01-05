// ================= PROCTOR DASHBOARD =================

// ---------- PeerJS ----------
const peer = new Peer({
  host: "0.peerjs.com",
  port: 443,
  secure: true
});
let peerReady = false;
let activeConnections = new Map();
let connectionStates = new Map();
let studentSessions = new Map();

const studentGallery = document.getElementById("studentGallery");

// Connection state management
function saveConnectionState() {
  const state = {
    activeConnections: Array.from(activeConnections.keys()),
    connectionStates: Object.fromEntries(connectionStates),
    timestamp: Date.now()
  };
  try {
    sessionStorage.setItem('proctorConnectionState', JSON.stringify(state));
  } catch (e) { console.warn('Failed to save connection state:', e); }
}

function loadConnectionState() {
  try {
    const saved = sessionStorage.getItem('proctorConnectionState');
    if (saved) {
      const state = JSON.parse(saved);
      // Only restore if less than 5 minutes old
      if (Date.now() - state.timestamp < 300000) {
        return state;
      }
    }
  } catch (e) { console.warn('Failed to load connection state:', e); }
  return null;
}

// Add manual test button to force connection
function addTestButton() {
  if (document.getElementById('forceConnectBtn')) return;

  const btn = document.createElement('button');
  btn.id = 'forceConnectBtn';
  btn.textContent = 'Force Connect Students';
  btn.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;padding:10px;background:orange;color:white;border:none;cursor:pointer;';
  btn.onclick = forceConnectStudents;
  document.body.appendChild(btn);
  
  // Add debug button
  const debugBtn = document.createElement('button');
  debugBtn.id = 'debugBtn';
  debugBtn.textContent = 'Debug State';
  debugBtn.style.cssText = 'position:fixed;top:60px;right:10px;z-index:9999;padding:10px;background:purple;color:white;border:none;cursor:pointer;';
  debugBtn.onclick = debugCurrentState;
  document.body.appendChild(debugBtn);
}

function debugCurrentState() {
  console.log('=== DEBUG STATE ===');
  console.log('Active Connections:', Array.from(activeConnections.keys()));
  console.log('Connection States:', Object.fromEntries(connectionStates));
  console.log('Student Sessions:', Object.fromEntries(studentSessions));
  console.log('Cards in DOM:', Array.from(document.querySelectorAll('.student-card')).map(c => c.id));
  console.log('Videos with streams:', Array.from(document.querySelectorAll('video')).filter(v => v.srcObject).length);
  console.log('==================');
}

function forceConnectStudents() {
  fetch('/trigger-student-reconnect', { method: 'POST' });
  setTimeout(fetchActiveStudents, 1000);
}

// When admin PeerJS is ready
peer.on("open", (adminPeerId) => {
  console.log("Proctor Peer ID:", adminPeerId);
  peerReady = true;

  addTestButton();

  // Register as proctor
  fetch("/store-peer-id", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ peerId: adminPeerId, type: "proctor" })
  }).then(() => {
    // Restore previous connection state if available
    const savedState = loadConnectionState();
    if (savedState) {
      console.log('🔄 Restoring connection state:', savedState);
      savedState.activeConnections.forEach(peerId => {
        connectionStates.set(peerId, savedState.connectionStates[peerId] || 'disconnected');
      });
    }
    
    // Trigger student reconnections
    fetch('/trigger-student-reconnect', { method: 'POST' })
      .catch(err => console.warn('Failed to trigger reconnect:', err));
    
    fetchActiveStudents();

    // Refresh student list every 5 seconds
    setInterval(fetchActiveStudents, 5000);
  }).catch(err => console.error("Failed to register proctor:", err));
});

// Reconnect when page becomes visible (returning from violations page)
document.addEventListener('visibilitychange', function () {
  if (!document.hidden && peerReady) {
    console.log('🔄 Page visible again, restoring connections...');
    setTimeout(() => {
      restoreConnections();
      fetchActiveStudents();
    }, 1000);
  }
});

// Restore connections for existing peer IDs
function restoreConnections() {
  connectionStates.forEach((state, peerId) => {
    const card = document.getElementById(`card-${peerId}`);
    if (card && state === 'connected') {
      const video = card.querySelector('video');
      if (!video.srcObject) {
        console.log('🔄 Attempting to restore connection for:', peerId);
        // Mark as needing reconnection
        connectionStates.set(peerId, 'reconnecting');
        card.querySelector('.violation').innerText = '🔄 Reconnecting...';
      }
    }
  });
  saveConnectionState();
}


// Fetch active student sessions
function fetchActiveStudents() {
  fetch("/get-student-sessions")
    .then(res => res.json())
    .then(sessions => {
      console.log("📋 Active student sessions:", sessions);

      Object.entries(sessions).forEach(([email, session]) => {
        const peerId = session.peerId;
        let card = document.getElementById(`card-${email}`);
        
        // Check if there's a temporary card for this peer ID
        const tempCard = document.getElementById(`card-temp-${peerId}`);
        
        if (tempCard && !card) {
          // Replace temporary card with proper card
          console.log(`🔄 Converting temporary card to proper card for ${email}`);
          
          // Get the video element from temp card
          const tempVideo = tempCard.querySelector('video');
          const hasStream = tempVideo && tempVideo.srcObject;
          
          // Remove temp card
          tempCard.remove();
          
          // Create proper card
          createStudentCard(email, session.name, peerId);
          card = document.getElementById(`card-${email}`);
          
          // Restore stream if it existed
          if (hasStream && card) {
            const newVideo = card.querySelector('video');
            if (newVideo) {
              newVideo.srcObject = tempVideo.srcObject;
              newVideo.play().then(() => {
                console.log('✅ Stream restored to proper card');
                card.querySelector('.violation').innerText = '🟢 Connected';
              });
            }
          }
          
          // Remove from temp sessions
          const tempEmail = `temp-${peerId}`;
          studentSessions.delete(tempEmail);
        } else if (!card) {
          createStudentCard(email, session.name, peerId);
          connectionStates.set(peerId, 'connecting');
        } else {
          updateStudentCard(email, session.name, peerId);
        }
        
        studentSessions.set(email, session);
      });

      // Remove inactive students (but keep temp cards with active streams)
      const existingCards = document.querySelectorAll('.student-card');
      existingCards.forEach(card => {
        const cardId = card.id;
        
        if (cardId.startsWith('card-temp-')) {
          // Keep temp cards that have active streams
          const video = card.querySelector('video');
          if (!video || !video.srcObject) {
            card.remove();
            const tempEmail = cardId.replace('card-', '');
            studentSessions.delete(tempEmail);
          }
        } else {
          const cardEmail = cardId.replace('card-', '');
          if (!sessions[cardEmail]) {
            const session = studentSessions.get(cardEmail);
            if (session) {
              activeConnections.delete(session.peerId);
              connectionStates.delete(session.peerId);
            }
            card.remove();
            studentSessions.delete(cardEmail);
          }
        }
      });
      
      saveConnectionState();
    })
    .catch(err => console.error("Failed to fetch student sessions", err));
}


// Create student card
function createStudentCard(email, name, peerId) {
  const card = document.createElement("div");
  card.className = "student-card";
  card.id = `card-${email}`;

  card.innerHTML = `
    <video autoplay playsinline muted></video>
    <div class="info">
      <div class="student-name">${name}</div>
      <div class="student-email">${email}</div>
      <div class="peer-id">Peer ID: ${peerId}</div>
    </div>
    <div class="violation">🟢 Live</div>
    <div class="card-buttons">
      <button class="view-violations" onclick="viewViolations('${peerId}')">
        <i class="fas fa-exclamation-triangle"></i> View Violations
      </button>
    </div>
  `;

  studentGallery.appendChild(card);
}

// Update student card
function updateStudentCard(email, name, peerId) {
  const card = document.getElementById(`card-${email}`);
  if (card) {
    const peerIdDiv = card.querySelector('.peer-id');
    const violationsBtn = card.querySelector('.view-violations');
    
    if (peerIdDiv) peerIdDiv.textContent = `Peer ID: ${peerId}`;
    if (violationsBtn) violationsBtn.setAttribute('onclick', `viewViolations('${peerId}')`);
  }
}

// View violations for specific peer using modal
function viewViolations(peerId) {
  // Show modal
  const modal = document.getElementById('violationsModal');
  const modalPeerId = document.getElementById('modalPeerId');
  const violationsContent = document.getElementById('violationsContent');

  modalPeerId.textContent = peerId;
  violationsContent.innerHTML = '<div style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin"></i> Loading violations...</div>';

  modal.style.display = 'block';

  // Fetch violations data via API
  fetch(`/api/violations/${peerId}`)
    .then(response => response.json())
    .then(data => {
      if (data.violations && data.violations.length > 0) {
        let tableHTML = `
          <table class="violations-table">
            <thead>
              <tr>
                <th>Peer ID</th>
                <th>Violation Time</th>
                <th>Reasons</th>
              </tr>
            </thead>
            <tbody>
        `;

        data.violations.forEach(log => {
          tableHTML += `
            <tr>
              <td>${log.peer_id || 'N/A'}</td>
              <td>${log.time || log.timestamp || 'N/A'}</td>
              <td>
                <ul>
          `;

          if (log.reasons && log.reasons.length > 0) {
            log.reasons.forEach(reason => {
              tableHTML += `<li>${reason}</li>`;
            });
          } else {
            tableHTML += '<li>No specific reason recorded</li>';
          }

          tableHTML += `
                </ul>
              </td>
            </tr>
          `;
        });

        tableHTML += `
            </tbody>
          </table>
        `;

        violationsContent.innerHTML = tableHTML;
      } else {
        violationsContent.innerHTML = '<div class="no-violations">🚫 No violation logs found for this student.</div>';
      }
    })
    .catch(error => {
      console.error('Error loading violations:', error);
      violationsContent.innerHTML = '<div class="no-violations">❌ Error loading violations. Please try again.</div>';
    });
}

// Close violations modal
function closeViolationsModal() {
  document.getElementById('violationsModal').style.display = 'none';
}

// Close modal when clicking outside or pressing Escape
window.onclick = function (event) {
  const modal = document.getElementById('violationsModal');
  if (event.target === modal) {
    closeViolationsModal();
  }
}

// Close modal with Escape key
document.addEventListener('keydown', function (event) {
  if (event.key === 'Escape') {
    const modal = document.getElementById('violationsModal');
    if (modal.style.display === 'block') {
      closeViolationsModal();
    }
  }
});

// Handle incoming calls from students
peer.on("call", (call) => {
  console.log("📞 Incoming call from:", call.peer);

  call.answer();
  activeConnections.set(call.peer, call);
  connectionStates.set(call.peer, 'connecting');

  call.on("stream", (stream) => {
    console.log("🎥 Stream received from:", call.peer);

    // Find card by peer ID - try multiple approaches
    let card = null;
    let studentEmail = null;
    
    // Method 1: Search through existing sessions
    studentSessions.forEach((session, email) => {
      if (session.peerId === call.peer) {
        card = document.getElementById(`card-${email}`);
        studentEmail = email;
      }
    });
    
    // Method 2: If no card found, create a temporary one
    if (!card) {
      console.log("No existing card found for peer:", call.peer, "- creating temporary card");
      
      // Create a temporary card with peer ID as identifier
      studentEmail = `temp-${call.peer}`;
      createStudentCard(studentEmail, `Student (${call.peer.substring(0, 8)})`, call.peer);
      card = document.getElementById(`card-${studentEmail}`);
      
      // Store in sessions for future reference
      studentSessions.set(studentEmail, {
        peerId: call.peer,
        name: `Student (${call.peer.substring(0, 8)})`,
        email: studentEmail
      });
    }
    
    if (!card) {
      console.error("Failed to create or find card for peer:", call.peer);
      return;
    }

    const video = card.querySelector("video");
    const violationDiv = card.querySelector(".violation");

    if (!video) {
      console.error("No video element found in card for peer:", call.peer);
      return;
    }

    console.log("Setting up video for peer:", call.peer, "Card ID:", card.id);
    video.srcObject = stream;
    video.muted = true;
    
    // Add additional video attributes for better compatibility
    video.setAttribute('playsinline', 'true');
    video.setAttribute('autoplay', 'true');
    
    video.play().then(() => {
      console.log("✅ Video playing successfully for:", call.peer);
      violationDiv.innerText = "🟢 Connected";
      connectionStates.set(call.peer, 'connected');
      saveConnectionState();
    }).catch(err => {
      console.warn("Autoplay blocked for:", call.peer, err);
      violationDiv.innerText = "⚠️ Click to play";
      connectionStates.set(call.peer, 'ready');

      video.onclick = () => {
        video.play().then(() => {
          console.log("✅ Manual play successful for:", call.peer);
          violationDiv.innerText = "🟢 Connected";
          connectionStates.set(call.peer, 'connected');
          saveConnectionState();
          video.onclick = null;
        }).catch(playErr => {
          console.error("Manual play failed for:", call.peer, playErr);
          violationDiv.innerText = "🔴 Play failed";
        });
      };
    });
  });

  call.on("error", (err) => {
    console.error("❌ Call error for", call.peer, err);
    
    // Find the card for this peer (including temporary ones)
    let targetCard = null;
    studentSessions.forEach((session, email) => {
      if (session.peerId === call.peer) {
        targetCard = document.getElementById(`card-${email}`);
      }
    });
    
    if (targetCard) {
      const violationDiv = targetCard.querySelector(".violation");
      if (violationDiv) violationDiv.innerText = "🔴 Connection error";
    }
    
    connectionStates.set(call.peer, 'error');
    activeConnections.delete(call.peer);
    saveConnectionState();
  });

  call.on("close", () => {
    console.log("📞 Call closed for:", call.peer);
    
    // Find the card for this peer (including temporary ones)
    let targetCard = null;
    studentSessions.forEach((session, email) => {
      if (session.peerId === call.peer) {
        targetCard = document.getElementById(`card-${email}`);
      }
    });
    
    if (targetCard) {
      const violationDiv = targetCard.querySelector(".violation");
      if (violationDiv) violationDiv.innerText = "🔴 Disconnected";
    }
    
    connectionStates.set(call.peer, 'disconnected');
    activeConnections.delete(call.peer);
    saveConnectionState();
  });
});

// Request connection from student (student will call us back)
function callStudent(studentPeerId) {
  console.log("📞 Requesting connection from:", studentPeerId);
  // Just create the card - student will initiate the call
}


// ================= BACKGROUND ANIMATION =================

const canvas = document.getElementById("bgCanvas");
const ctx = canvas.getContext("2d");
let w, h;
let mouse = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
let lines = [];

function resize() {
  w = canvas.width = window.innerWidth;
  h = canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

window.addEventListener("mousemove", (e) => {
  mouse.x = e.clientX;
  mouse.y = e.clientY;
  const moveX = (mouse.x / window.innerWidth) * 100;
  const moveY = (mouse.y / window.innerHeight) * 100;
  canvas.style.background = `radial-gradient(circle at ${moveX}% ${moveY}%, #b8dbff, #f3f8ff 85%)`;
});

for (let i = 0; i < 120; i++) {
  lines.push({
    x: Math.random() * w,
    y: Math.random() * h,
    dx: (Math.random() - 0.5) * 1.5,
    dy: (Math.random() - 0.5) * 1.5,
    hue: 210 + Math.random() * 40
  });
}

function draw() {
  ctx.clearRect(0, 0, w, h);
  const glow = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 200);
  glow.addColorStop(0, "rgba(0, 123, 255, 0.08)");
  glow.addColorStop(1, "rgba(255, 255, 255, 0)");
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, w, h);

  lines.forEach(l => {
    l.x += l.dx;
    l.y += l.dy;
    if (l.x < 0 || l.x > w) l.dx *= -1;
    if (l.y < 0 || l.y > h) l.dy *= -1;
    ctx.beginPath();
    const x2 = l.x + Math.sin(Date.now() * 0.0015 + l.x * 0.02) * 35;
    const y2 = l.y + Math.cos(Date.now() * 0.0015 + l.y * 0.02) * 35;
    ctx.moveTo(l.x, l.y);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = `hsla(${l.hue}, 100%, 50%, 0.2)`;
    ctx.lineWidth = 1;
    ctx.stroke();
  });

  requestAnimationFrame(draw);
}
draw();
