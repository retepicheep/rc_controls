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