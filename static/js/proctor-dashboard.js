// ================= PROCTOR DASHBOARD =================

// ---------- PeerJS ----------
const peer = new Peer({
  host: "0.peerjs.com",
  port: 443,
  secure: true
});
let peerReady = false;

const studentGallery = document.getElementById("studentGallery");

// Add manual test button to force connection
function addTestButton() {
  if (document.getElementById('forceConnectBtn')) return;

  const btn = document.createElement('button');
  btn.id = 'forceConnectBtn';
  btn.textContent = 'Force Connect Students';
  btn.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;padding:10px;background:orange;color:white;border:none;cursor:pointer;';
  btn.onclick = forceConnectStudents;
  document.body.appendChild(btn);
}

function forceConnectStudents() {
  fetch('/request-reconnect', { method: 'POST' });
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
    fetchActiveStudents();

    // Refresh student list every 5 seconds
    setInterval(fetchActiveStudents, 5000);
  }).catch(err => console.error("Failed to register proctor:", err));
});

// Reconnect when page becomes visible (returning from violations page)
document.addEventListener('visibilitychange', function () {
  if (!document.hidden && peerReady) {
    console.log('🔄 Page visible again, refreshing connections...');
    setTimeout(() => {
      fetchActiveStudents();
    }, 1000);
  }
});


// Fetch active student peer IDs
function fetchActiveStudents() {
  fetch("/get-peer-ids")
    .then(res => res.json())
    .then(peerIds => {
      console.log("📋 Active students:", peerIds);

      // Only add new students, don't recreate existing cards
      peerIds.forEach(peerId => {
        if (!document.getElementById(`card-${peerId}`)) {
          createStudentCard(peerId);
          callStudent(peerId);
        }
      });

      // Remove cards for students no longer active
      const existingCards = document.querySelectorAll('.student-card');
      existingCards.forEach(card => {
        const cardPeerId = card.id.replace('card-', '');
        if (!peerIds.includes(cardPeerId)) {
          card.remove();
        }
      });
    })
    .catch(err => console.error("Failed to fetch peer IDs", err));
}


// Create UI card
function createStudentCard(peerId) {
  const card = document.createElement("div");
  card.className = "student-card";
  card.id = `card-${peerId}`;

  card.innerHTML = `
    <video autoplay playsinline muted></video>
    <div class="info">Peer ID: ${peerId}</div>
    <div class="violation">🟢 Live</div>
    <div class="card-buttons">
      <button class="view-violations" onclick="viewViolations('${peerId}')">
        <i class="fas fa-exclamation-triangle"></i> View Violations
      </button>
    </div>
  `;

  studentGallery.appendChild(card);
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

  // Answer the call (proctor doesn't need to send video)
  call.answer();

  call.on("stream", (stream) => {
    console.log("🎥 Stream received from:", call.peer);

    let card = document.getElementById(`card-${call.peer}`);
    if (!card) {
      console.log("Creating card for new peer:", call.peer);
      createStudentCard(call.peer);
      card = document.getElementById(`card-${call.peer}`);
    }

    if (card) {
      const video = card.querySelector("video");
      const violationDiv = card.querySelector(".violation");

      

      video.srcObject = stream;
      video.muted = true;
      video.play().then(() => {
        console.log("✅ Video playing for:", call.peer);
        violationDiv.innerText = "🟢 Connected";
      }).catch(err => {
        console.warn("Autoplay blocked:", err);
        violationDiv.innerText = "⚠️ Click to play";

        // Add click handler to manually start video
        video.onclick = () => {
          video.play().then(() => {
            violationDiv.innerText = "🟢 Connected";
            video.onclick = null;
          });
        };
      });
    }
  });

  call.on("error", (err) => {
    console.error("❌ Call error for", call.peer, err);
    const card = document.getElementById(`card-${call.peer}`);
    if (card) {
      card.querySelector(".violation").innerText = "🔴 Connection error";
    }
  });

  call.on("close", () => {
    console.log("📞 Call closed for:", call.peer);
    const card = document.getElementById(`card-${call.peer}`);
    if (card) {
      card.querySelector(".violation").innerText = "🔴 Disconnected";
    }
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
