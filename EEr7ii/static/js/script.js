// Matrix animation script
const canvas = document.getElementById('matrix');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const columns = Math.floor(canvas.width / 20);
const rows = Math.floor(canvas.height / 20);
const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
const charArray = chars.split('');
const drops = Array(columns).fill(0);

function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)'; // More transparent background
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#0F0'; // Green color
    ctx.font = '20px monospace';
    
    for (let i = 0; i < drops.length; i++) {
        const char = charArray[Math.floor(Math.random() * charArray.length)];
        ctx.fillText(char, i * 20, drops[i] * 20);
        
        if (drops[i] * 20 > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        }
        
        drops[i]++;
    }
}

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    draw();
}

window.addEventListener('resize', resize);
setInterval(draw, 50);
