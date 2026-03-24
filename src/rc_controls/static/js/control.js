const keyMap = {
    "w": "w",
    "a": "a",
    "s": "s",
    "d": "d",
    " ": "space",
    "Shift": "shift"
};

const pressed = new Set();
let websocket;

window.addEventListener("DOMContentLoaded", () => {
    websocket = new WebSocket(`ws://${window.location.hostname}:8001/`);
});

document.addEventListener("keydown", e => {
    const cmd = keyMap[e.key];
    if (cmd) {
        pressed.add(cmd);
        sendCommands();
    }
});

document.addEventListener("keyup", e => {
    const cmd = keyMap[e.key];
    if (cmd) {
        pressed.delete(cmd);

        if (["w", "s"].includes(e.key)) pressed.add("stop drive");
        if (["a", "d"].includes(e.key)) pressed.add("stop rotate");

        sendCommands();

        pressed.delete("stop drive");
        pressed.delete("stop rotate");
    }
});

function sendCommands() {
    if (websocket?.readyState === WebSocket.OPEN) {
        const payload = JSON.stringify([...pressed]);
        console.log("sending:", payload);
        websocket.send(payload);
    }
}

function recieveSysData() {
    try {
        websocket.addEventListener("message", ({ data }) => {
            document.getElementById("cpu-temp").innerText = "Temp: CPU: " + data.cpu_temp;
            document.getElementById("cpu-load").innerText = "Load: SYS: " + data.cpu_load;
            document.getElementById("wifi-strength").innerText = "Connection: LINK: " + data.wifi_strength;
        });
    } catch (err) {
        console.error("Failed to fetch system health:", err);
    }
}