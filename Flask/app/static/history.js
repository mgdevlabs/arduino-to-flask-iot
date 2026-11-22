let historyPoints = [];

function drawChart(canvasId, key, color) {
    const canvas = document.getElementById(canvasId);
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const points = historyPoints.filter(p => typeof p[key] === "number");
    if (!points.length) {
        ctx.fillStyle = "#4d88b8";
        ctx.font = '12px "Fira Code", monospace';
        ctx.fillText("NO DATA", 8, height / 2);
        return;
    }

    const values = points.map(p => p[key]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1 || 1;
    const low = min - padding;
    const high = max + padding;

    const first = points[0].ts * 1000;
    const last = points[points.length - 1].ts * 1000;
    const span = last - first || 1;

    const xFor = ts => ((ts * 1000 - first) / span) * width;
    const yFor = value => height - ((value - low) / (high - low)) * height;

    ctx.strokeStyle = "rgba(80, 190, 255, 0.12)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    ctx.fillStyle = "#4d88b8";
    ctx.font = '10px "Fira Code", monospace';
    ctx.fillText(max.toFixed(1), 4, 12);
    ctx.fillText(min.toFixed(1), 4, height - 4);

    ctx.beginPath();
    if (points.length === 1) {
        ctx.arc(width / 2, yFor(points[0][key]), 3, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        return;
    }

    points.forEach((point, index) => {
        const x = xFor(point.ts);
        const y = yFor(point[key]);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
    ctx.stroke();
    ctx.shadowBlur = 0;
}

function drawAll() {
    drawChart("temp-chart", "temperature", "#21d4fd");
    drawChart("humi-chart", "humidity", "#7fc9ff");
}

async function loadHistory() {
    try {
        const response = await fetch("/api/history");
        historyPoints = await response.json();
        drawAll();
    } catch (error) {
        console.error("Error while loading history", error);
    }
}

loadHistory();
setInterval(loadHistory, 60000);
window.addEventListener("resize", drawAll);
