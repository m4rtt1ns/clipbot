import socket, threading, time
import numpy as np


class TwitchChat(threading.Thread):
    """Conta mensagens do chat por segundo (leitura anonima, sem login)."""

    def __init__(self, channel):
        super().__init__(daemon=True)
        self.channel = channel.lower().lstrip("@")
        self.t0 = time.time()
        self.stamps = []
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            try:
                s = socket.create_connection(("irc.chat.twitch.tv", 6667), timeout=30)
                s.sendall(b"PASS SCHMOOPIIE\r\nNICK justinfan48213\r\n")
                s.sendall(f"JOIN #{self.channel}\r\n".encode())
                s.settimeout(120)
                buf = ""
                while not self.stop_flag:
                    data = s.recv(4096).decode("utf-8", "ignore")
                    if not data:
                        break
                    buf += data
                    while "\r\n" in buf:
                        line, buf = buf.split("\r\n", 1)
                        if line.startswith("PING"):
                            s.sendall(b"PONG :tmi.twitch.tv\r\n")
                        elif " PRIVMSG " in line:
                            self.stamps.append(time.time() - self.t0)
            except Exception:
                time.sleep(3)

    def per_second(self, n):
        c = np.zeros(n)
        for t in self.stamps:
            i = int(t)
            if 0 <= i < n:
                c[i] += 1
        return c
