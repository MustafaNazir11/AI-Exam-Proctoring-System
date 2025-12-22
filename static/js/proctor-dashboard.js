// ================= PROCTOR DASHBOARD =================

// ---------- PeerJS ----------
const peer = new Peer({
  host: "0.peerjs.com",
  port: 443,
  secure: true
});
let peerReady = false;

const studentGallery = document.getElementById("studentGallery");

// When admin PeerJS is ready
peer.on("open", (adminPeerId) => {
  console.log("Proctor Peer ID:", adminPeerId);
  peerReady = true;
  fetchActiveStudents();
});


// Fetch active student peer IDs
function fetchActiveStudents() {
  fetch("/get-peer-ids")
    .then(res => res.json())
    .then(peerIds => {
      studentGallery.innerHTML = "";

      peerIds.forEach(peerId => {
        if (!document.getElementById(`card-${peerId}`)) {
          createStudentCard(peerId);

          // ⏱️ small delay avoids race condition
          setTimeout(() => {
            callStudent(peerId);
          }, 800);
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
  `;

  studentGallery.appendChild(card);
}

// Call student & attach stream
function callStudent(studentPeerId) {
  if (!peerReady) {
    console.warn("Peer not ready yet");
    return;
  }

  const call = peer.call(studentPeerId, null);

  // 🔒 SAFETY CHECK (THIS FIXES YOUR ERROR)
  if (!call) {
    console.warn("Call failed for:", studentPeerId);
    return;
  }

  call.on("stream", (stream) => {
    const card = document.getElementById(`card-${studentPeerId}`);
    if (!card) return;

    const video = card.querySelector("video");
    video.srcObject = stream;
  });

  call.on("error", err => {
    console.error("Call error:", err);
  });

  call.on("close", () => {
    const card = document.getElementById(`card-${studentPeerId}`);
    if (card) {
      card.querySelector(".violation").innerText = "🔴 Disconnected";
    }
  });
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
