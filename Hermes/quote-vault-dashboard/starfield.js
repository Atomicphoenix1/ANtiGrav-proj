// Starfield background for the Cosmic Alchemist Quote Dashboard
// Renders subtle, drifting, and twinkling stars on a canvas element.

window.initStarfield = function() {
  const canvas = document.getElementById('starfield');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let stars = [];
  let animationFrameId;

  // Configuration
  const STAR_COUNT = 120;
  const SPEED = 0.05; // Gentle drift speed
  const COLORS = [
    'rgba(255, 255, 255, 0.8)',      // Soft white
    'rgba(173, 216, 230, 0.7)',      // Soft cyan-blue
    'rgba(221, 160, 221, 0.6)',      // Soft violet
    'rgba(255, 223, 186, 0.7)',      // Soft golden-amber
  ];

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    initStars();
  }

  function initStars() {
    stars = [];
    for (let i = 0; i < STAR_COUNT; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.5 + 0.5,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinklePhase: Math.random() * Math.PI,
        angle: Math.random() * Math.PI * 2, // Drift direction
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw space dust gradients (subtle glow spots in the background)
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const gradient = ctx.createRadialGradient(
      centerX, centerY, 10,
      centerX, centerY, Math.max(canvas.width, canvas.height) * 0.8
    );
    gradient.addColorStop(0, 'rgba(30, 15, 60, 0.25)'); // Cosmic purple glow center
    gradient.addColorStop(0.5, 'rgba(10, 15, 35, 0.1)');
    gradient.addColorStop(1, 'rgba(5, 5, 15, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw and update stars
    for (let i = 0; i < stars.length; i++) {
      const star = stars[i];

      // Update twinkle intensity
      star.twinklePhase += star.twinkleSpeed;
      const alphaMultiplier = Math.abs(Math.sin(star.twinklePhase));

      // Draw Star
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fillStyle = star.color.replace(/[\d.]+\)$/, `${alphaMultiplier})`);
      ctx.shadowBlur = star.size * 3;
      ctx.shadowColor = star.color;
      ctx.fill();
      ctx.shadowBlur = 0; // Reset shadow

      // Drift physics (slowly float stars across space)
      star.x += Math.cos(star.angle) * SPEED;
      star.y += Math.sin(star.angle) * SPEED;

      // Wrap around screen borders
      if (star.x < 0) star.x = canvas.width;
      if (star.x > canvas.width) star.x = 0;
      if (star.y < 0) star.y = canvas.height;
      if (star.y > canvas.height) star.y = 0;
    }

    animationFrameId = requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  draw();

  // Return teardown function if needed
  return () => {
    cancelAnimationFrame(animationFrameId);
    window.removeEventListener('resize', resizeCanvas);
  };
}
