// === Upload Buttons ===
document.getElementById('uploadBtn').onclick = () => {
  window.location.href = '/input_questions';
};
document.getElementById('monitorBtn').onclick = () => {
  window.location.href = 'http://127.0.0.1:5000/dashboard';
};

// === Logout Button ===
document.getElementById('logoutBtn').onclick = () => {
  if (confirm("Are you sure you want to logout?")) {
    window.location.href = "http://127.0.0.1:5000/login";
  }
};

// === Counter Animation ===
const counters = [
  { id: "activeExams", end: 23 },
  { id: "totalStudents", end: 142 },
  { id: "suspiciousActivities", end: 4 }
];
counters.forEach(c => {
  let n = 0;
  const el = document.getElementById(c.id);
  const tick = () => {
    n += c.end / 50;
    if (n < c.end) {
      el.textContent = Math.ceil(n);
      requestAnimationFrame(tick);
    } else {
      el.textContent = c.end;
    }
  };
  tick();
});

// === Animated Background ===
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
  const moveX = (e.clientX - mouse.x) * 0.01;
  const moveY = (e.clientY - mouse.y) * 0.01;
  lines.push({ x: mouse.x, y: mouse.y, vx: moveX, vy: moveY, life: 1 });
});

function createLine() {
  lines.push({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 2,
    vy: (Math.random() - 0.5) * 2,
    life: Math.random()
  });
}

function animate() {
  ctx.fillStyle = "rgba(248, 250, 252, 0.1)";
  ctx.fillRect(0, 0, w, h);

  if (Math.random() < 0.03) createLine();

  lines.forEach((line, i) => {
    line.x += line.vx;
    line.y += line.vy;
    line.life -= 0.01;

    if (line.life <= 0 || line.x < 0 || line.x > w || line.y < 0 || line.y > h) {
      lines.splice(i, 1);
      return;
    }

    const alpha = line.life * 0.8;
    ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(line.x, line.y, 1, 0, Math.PI * 2);
    ctx.stroke();
  });

  requestAnimationFrame(animate);
}
animate();