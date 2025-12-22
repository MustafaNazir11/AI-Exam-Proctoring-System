// Minimal preview page functionality
(() => {
  "use strict";

  const webcam = document.getElementById("webcam");
  const proceedBtn = document.getElementById("proceedBtn");
  const previewBtn = document.getElementById("previewBtn");

  // ------------------ Preview Camera ------------------
  if (previewBtn) {
    previewBtn.addEventListener('click', async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (webcam) {
          webcam.srcObject = stream;
          console.log("📹 Camera preview started");
        }
      } catch (err) {
        alert('Camera access denied or not available.');
      }
    });
  }

  // ------------------ Start Exam Navigation ------------------
  if (proceedBtn) {
    proceedBtn.addEventListener("click", () => {
      // Simply navigate to exam page - all peer logic will be handled there
      window.location.href = "/exam";
    });
  }

})();

// === Background Animation ===
document.addEventListener('DOMContentLoaded', function() {
  const canvas = document.getElementById("bgCanvas");
  if (!canvas) return;
  
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
});