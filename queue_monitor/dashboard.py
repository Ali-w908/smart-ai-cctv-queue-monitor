def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Queue Monitoring System</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0d0d12;
            --bg-surface: #16161e;
            --border-color: #25253a;
            --text-primary: #f0f0f5;
            --text-secondary: #a0a0b8;
            --accent-cyan: #00c8ff;
            --accent-green: #00ffb2;
            --accent-danger: #ff5e7a;
            --accent-warning: #ffc107;
            --accent-orange: #ff9800;
            --badge-empty: #555555;
            --font-family: 'Inter', sans-serif;
            --transition-speed: 0.3s;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            font-family: var(--font-family);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Tabular numerals for numbers */
        .num {
            font-variant-numeric: tabular-nums;
        }

        /* HEADER */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 2rem;
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-color);
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--accent-green);
            font-weight: 500;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-green);
            animation: pulse-green 2s infinite;
        }

        .tech-badge {
            background-color: rgba(0, 200, 255, 0.1);
            color: var(--accent-cyan);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid rgba(0, 200, 255, 0.3);
        }

        .header-right {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        /* TOP AGGREGATE BAR */
        .kpi-container {
            display: flex;
            gap: 1.5rem;
            padding: 1.5rem 2rem;
            flex-wrap: wrap;
        }

        .kpi-card {
            flex: 1;
            min-width: 200px;
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            transition: transform var(--transition-speed);
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
        }

        .kpi-title {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .kpi-unit {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 400;
        }

        /* CAMERA GRID */
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 1.5rem;
            padding: 0 2rem 2rem 2rem;
            flex: 1;
        }

        .camera-tile {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .feed-container {
            position: relative;
            width: 100%;
            aspect-ratio: 16 / 9;
            background-color: #000;
            overflow: hidden;
        }

        .feed-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .feed-overlay-top {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%);
            pointer-events: none;
        }

        .camera-name {
            font-weight: 600;
            font-size: 1.125rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.8);
        }

        .cam-status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            backdrop-filter: blur(4px);
        }

        .cam-status-online {
            background-color: rgba(0, 255, 178, 0.2);
            color: var(--accent-green);
            border: 1px solid rgba(0, 255, 178, 0.4);
        }

        .cam-status-offline {
            background-color: rgba(255, 94, 122, 0.2);
            color: var(--accent-danger);
            border: 1px solid rgba(255, 94, 122, 0.4);
        }

        .cam-status-connecting {
            background-color: rgba(255, 193, 7, 0.2);
            color: var(--accent-warning);
            border: 1px solid rgba(255, 193, 7, 0.4);
            animation: blink 1s infinite;
        }

        .stats-bar {
            padding: 1rem;
            background-color: rgba(22, 22, 30, 0.8);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .stats-metrics {
            display: flex;
            gap: 1.5rem;
        }

        .metric {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .metric-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-value {
            font-size: 1.125rem;
            font-weight: 600;
        }

        .queue-status-badge {
            padding: 0.35rem 0.85rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .qs-empty { background-color: var(--badge-empty); color: #fff; }
        .qs-low { background-color: rgba(0, 255, 178, 0.15); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .qs-moderate { background-color: rgba(255, 193, 7, 0.15); color: var(--accent-warning); border: 1px solid var(--accent-warning); }
        .qs-high { background-color: rgba(255, 152, 0, 0.15); color: var(--accent-orange); border: 1px solid var(--accent-orange); }
        .qs-critical { 
            background-color: rgba(255, 94, 122, 0.15); 
            color: var(--accent-danger); 
            border: 1px solid var(--accent-danger);
            animation: pulse-red 1.5s infinite;
        }

        .details-section {
            padding: 1rem;
            display: flex;
            gap: 1rem;
            flex: 1;
        }

        .list-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .list-header {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        .list-content {
            font-size: 0.875rem;
            max-height: 120px;
            overflow-y: auto;
            padding-right: 0.5rem;
        }

        .list-content::-webkit-scrollbar {
            width: 4px;
        }
        .list-content::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        .list-item {
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid rgba(37, 37, 58, 0.5);
        }
        
        .list-item:last-child {
            border-bottom: none;
        }

        .id-badge {
            color: var(--accent-cyan);
            font-family: monospace;
        }

        /* FOOTER */
        footer {
            text-align: center;
            padding: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
            border-top: 1px solid var(--border-color);
            margin-top: auto;
        }

        /* ANIMATIONS */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 178, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(0, 255, 178, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 178, 0); }
        }

        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(255, 94, 122, 0.4); }
            70% { box-shadow: 0 0 0 8px rgba(255, 94, 122, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 94, 122, 0); }
        }

        @keyframes blink {
            50% { opacity: 0.5; }
        }
        
        /* Utility */
        .val-changed {
            animation: highlight 0.5s ease-out;
        }
        
        @keyframes highlight {
            0% { color: var(--accent-cyan); }
            100% { color: inherit; }
        }
    </style>
</head>
<body>

    <header>
        <div class="header-left">
            <h1>Queue Monitoring System</h1>
            <div class="live-indicator">
                <div class="pulse-dot"></div>
                LIVE
            </div>
            <div class="tech-badge">YOLOv8 + ByteTrack</div>
        </div>
        <div class="header-right" id="current-time">
            --:--:--
        </div>
    </header>

    <div class="kpi-container">
        <div class="kpi-card">
            <span class="kpi-title">Total People in Queue</span>
            <div><span class="kpi-value num" id="kpi-total-queue">0</span></div>
        </div>
        <div class="kpi-card">
            <span class="kpi-title">Average Wait Time</span>
            <div><span class="kpi-value num" id="kpi-avg-wait">0.0</span> <span class="kpi-unit">s</span></div>
        </div>
        <div class="kpi-card">
            <span class="kpi-title">Longest Wait Time</span>
            <div><span class="kpi-value num" id="kpi-longest-wait">0.0</span> <span class="kpi-unit">s</span></div>
        </div>
        <div class="kpi-card">
            <span class="kpi-title">Total Served Today</span>
            <div><span class="kpi-value num" id="kpi-total-served">0</span></div>
        </div>
    </div>

    <div class="camera-grid" id="camera-grid">
        <!-- Camera tiles will be dynamically inserted here -->
    </div>

    <footer>
        Queue Monitor &middot; Powered by Ultralytics YOLOv8 &amp; FastAPI
    </footer>

    <script>
        // Utilities
        function formatTime() {
            const now = new Date();
            return now.toLocaleTimeString('en-US', { hour12: false });
        }

        function updateClock() {
            document.getElementById('current-time').textContent = formatTime();
        }
        setInterval(updateClock, 1000);
        updateClock();
        
        function animateValueChange(element, newValue) {
            if (element.textContent !== String(newValue)) {
                element.textContent = newValue;
                element.classList.remove('val-changed');
                void element.offsetWidth; // trigger reflow
                element.classList.add('val-changed');
            }
        }
        
        function formatWait(seconds) {
            return parseFloat(seconds).toFixed(1);
        }

        // Camera Management
        const cameraGrid = document.getElementById('camera-grid');
        const cameraTiles = new Map();

        async function initCameras() {
            try {
                const res = await fetch('/api/cameras');
                const data = await res.json();
                
                data.cameras.forEach(cam => {
                    createCameraTile(cam);
                });
            } catch (err) {
                console.error("Failed to init cameras:", err);
            }
        }

        function createCameraTile(cam) {
            const tile = document.createElement('div');
            tile.className = 'camera-tile';
            tile.id = `cam-tile-${cam.id}`;
            
            tile.innerHTML = `
                <div class="feed-container">
                    <img src="/video_feed/${cam.id}" alt="Feed ${cam.id}" class="feed-img" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'100%\\' height=\\'100%\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%2316161e\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'%23555\\' text-anchor=\\'middle\\' dy=\\'.3em\\'>Feed Unavailable</text></svg>'">
                    <div class="feed-overlay-top">
                        <div class="camera-name">${cam.name}</div>
                        <div class="cam-status-badge cam-status-${cam.status}" id="cam-status-${cam.id}">${cam.status}</div>
                    </div>
                </div>
                <div class="stats-bar">
                    <div class="stats-metrics">
                        <div class="metric">
                            <span class="metric-label">Queue</span>
                            <span class="metric-value num" id="cam-qlen-${cam.id}">0</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg Wait</span>
                            <span class="metric-value num"><span id="cam-avg-${cam.id}">0.0</span>s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Longest</span>
                            <span class="metric-value num"><span id="cam-max-${cam.id}">0.0</span>s</span>
                        </div>
                    </div>
                    <div class="queue-status-badge qs-empty" id="cam-qstatus-${cam.id}">EMPTY</div>
                </div>
                <div class="details-section">
                    <div class="list-container">
                        <div class="list-header">Active Queue</div>
                        <div class="list-content" id="cam-active-${cam.id}"></div>
                    </div>
                    <div class="list-container">
                        <div class="list-header">Recent Exits</div>
                        <div class="list-content" id="cam-exits-${cam.id}"></div>
                    </div>
                </div>
            `;
            cameraGrid.appendChild(tile);
            cameraTiles.set(cam.id, tile);
        }

        function updateQueueStatusBadge(element, statusStr) {
            const status = (statusStr || 'empty').toLowerCase();
            element.className = `queue-status-badge qs-${status}`;
            element.textContent = status.toUpperCase();
        }

        function updateCamStatusBadge(element, statusStr) {
            const status = (statusStr || 'offline').toLowerCase();
            element.className = `cam-status-badge cam-status-${status}`;
            element.textContent = status.toUpperCase();
        }

        function renderList(container, items, isExit = false) {
            if (!items || items.length === 0) {
                container.innerHTML = '<div style="color:var(--text-secondary);font-size:0.75rem;padding:0.5rem 0;">None</div>';
                return;
            }
            container.innerHTML = items.map(item => `
                <div class="list-item">
                    <span class="id-badge">#${item.id}</span>
                    <span class="num">${formatWait(item.wait_seconds)}s</span>
                </div>
            `).join('');
        }

        // Stats Polling
        async function refreshStats() {
            try {
                const res = await fetch('/api/stats');
                if (!res.ok) return;
                const data = await res.json();
                
                // Update KPIs
                animateValueChange(document.getElementById('kpi-total-queue'), data.total_queue_length || 0);
                animateValueChange(document.getElementById('kpi-avg-wait'), formatWait(data.avg_wait || 0));
                animateValueChange(document.getElementById('kpi-longest-wait'), formatWait(data.longest_wait || 0));
                
                let totalServed = 0;

                // Update Cameras
                if (data.cameras) {
                    data.cameras.forEach(camData => {
                        totalServed += (camData.total_served || 0);
                        
                        const cid = camData.camera_id;
                        if (!cameraTiles.has(cid)) return; // Camera not in DOM yet
                        
                        // Metrics
                        animateValueChange(document.getElementById(`cam-qlen-${cid}`), camData.queue_length || 0);
                        animateValueChange(document.getElementById(`cam-avg-${cid}`), formatWait(camData.avg_wait || 0));
                        animateValueChange(document.getElementById(`cam-max-${cid}`), formatWait(camData.longest_wait || 0));
                        
                        // Badges
                        updateCamStatusBadge(document.getElementById(`cam-status-${cid}`), camData.camera_status);
                        updateQueueStatusBadge(document.getElementById(`cam-qstatus-${cid}`), camData.status);
                        
                        // Lists
                        renderList(document.getElementById(`cam-active-${cid}`), camData.active);
                        // Limit recent exits to last 5
                        const exits = camData.recent_exits || [];
                        renderList(document.getElementById(`cam-exits-${cid}`), exits.slice(0, 5), true);
                    });
                }
                
                animateValueChange(document.getElementById('kpi-total-served'), totalServed);
                
            } catch (err) {
                // Silently ignore poll errors to prevent console spam
            }
        }

        // Initialize and start loop
        initCameras().then(() => {
            setInterval(refreshStats, 500);
            refreshStats(); // initial fetch
        });

    </script>
</body>
</html>"""
