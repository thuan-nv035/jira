import { getToken } from "../utils/storage";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://127.0.0.1:8000";

export function createProjectSocket(projectId, onMessage, onStatus) {
  let socket = null;
  let pingTimer = null;
  let reconnectTimer = null;
  let closedByUser = false;
  let reconnectCount = 0;

  function cleanup() {
    if (pingTimer) clearInterval(pingTimer);
    if (reconnectTimer) clearTimeout(reconnectTimer);
    pingTimer = null;
    reconnectTimer = null;
  }

  function connect() {
    const token = getToken();
    if (!token || !projectId) return;

    cleanup();
    const url = `${WS_BASE_URL}/ws/projects/${projectId}?token=${encodeURIComponent(token)}`;
    socket = new WebSocket(url);
    onStatus?.("connecting");

    socket.onopen = () => {
      reconnectCount = 0;
      onStatus?.("connected");
      pingTimer = setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ event: "ping" }));
        }
      }, 25000);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        onMessage?.(payload);
      } catch {
        onMessage?.({ event: "raw", data: event.data });
      }
    };

    socket.onerror = () => {
      onStatus?.("error");
    };

    socket.onclose = () => {
      cleanup();
      onStatus?.("disconnected");
      if (!closedByUser) {
        reconnectCount += 1;
        const delay = Math.min(8000, 1000 * reconnectCount);
        reconnectTimer = setTimeout(connect, delay);
      }
    };
  }

  function close() {
    closedByUser = true;
    cleanup();
    if (socket) socket.close();
  }

  connect();

  return { close };
}
