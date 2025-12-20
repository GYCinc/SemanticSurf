// ui/whiteboard.js

// Liveblocks Public Key (From config or hardcoded for now - using the one seen in mcp_config)
const LB_PUBLIC_KEY = "pk_dev_..."; // We should fetch this securely if possible

let lbClient = null;
let room = null;
let canvas = null;
let ctx = null;
let isDrawing = false;
let currentRole = 'student'; // 'student' or 'teacher'
let currentColor = '#ffffff';
let currentStroke = 2;

async function initWhiteboard(studentId) {
    if (!studentId) return;
    
    // Initialize Liveblocks Client (using CDN loaded global)
    // Note: createClient should be available from the script tag in HTML
    if (typeof createClient === 'undefined') {
        console.error("Liveblocks client not loaded.");
        return;
    }

    lbClient = createClient({
        publicApiKey: "pk_dev_qGuV2VvEXcKEiH93Uw_jkCdM5QIo6r7I3XBb_EjFOMJQMgmScBWSGvOdzAzX_zAd" // From mcp_config dump
    });

    const roomId = `semantic-surfer-wb-${studentId}`;
    room = lbClient.enter(roomId, {
        initialPresence: { cursor: null },
        initialStorage: { strokes: new Liveblocks.LiveList() } // Correct usage
    });

    setupCanvas();
    bindEvents();
}

function setupCanvas() {
    const container = document.getElementById('wb-canvas-container');
    canvas = document.createElement('canvas');
    container.appendChild(canvas);
    ctx = canvas.getContext('2d');

    // Resize logic
    const resize = () => {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        redraw();
    };
    new ResizeObserver(resize).observe(container);
    resize();
}

function bindEvents() {
    // Local Drawing
    canvas.addEventListener('pointerdown', (e) => {
        isDrawing = true;
        const pt = getPoint(e);
        // Broadcast start
        if (room) {
            room.broadcastEvent({ type: 'draw_start', point: pt, color: currentColor, width: currentStroke });
        }
        ctx.beginPath();
        ctx.moveTo(pt.x, pt.y);
        ctx.strokeStyle = currentColor;
        ctx.lineWidth = currentStroke;
    });

    canvas.addEventListener('pointermove', (e) => {
        if (!isDrawing) return;
        const pt = getPoint(e);
        ctx.lineTo(pt.x, pt.y);
        ctx.stroke();
        
        if (room) {
            room.broadcastEvent({ type: 'draw_move', point: pt });
        }
    });

    canvas.addEventListener('pointerup', () => {
        isDrawing = false;
        if (room) room.broadcastEvent({ type: 'draw_end' });
    });

    // Remote Events
    if (room) {
        room.subscribe('event', ({ event }) => {
            if (event.type === 'draw_start') {
                ctx.beginPath();
                ctx.moveTo(event.point.x, event.point.y);
                ctx.strokeStyle = event.color;
                ctx.lineWidth = event.width;
            } else if (event.type === 'draw_move') {
                ctx.lineTo(event.point.x, event.point.y);
                ctx.stroke();
            }
        });
    }
}

function getPoint(e) {
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

function redraw() {
    // Re-render from history if we implement storage
}

// Global toggle
window.toggleWhiteboard = () => {
    const overlay = document.getElementById('wb-overlay');
    overlay.classList.toggle('active');
    
    // Init on first open if needed
    if (overlay.classList.contains('active') && !room) {
        const student = document.getElementById('student-selector').value;
        if (student) initWhiteboard(student);
    }
};
