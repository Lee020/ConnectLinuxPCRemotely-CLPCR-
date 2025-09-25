#!/bin/bash
# add "EMAIL"
# CONFIGURATION
PORT=9988
EMAIL="example1@gmail.com"
SUBJECT="Your Remote TTYD URL"

# 0. Kill any process already on port
echo "[*] Checking for existing process on port $PORT..."
PID=$(lsof -ti:$PORT)
if [[ -n "$PID" ]]; then
    echo "[*] Killing existing process on port $PORT (PID: $PID)..."
    kill -9 $PID
    sleep 1
fi

# 1. Start ttyd
echo "[+] Starting ttyd on port $PORT..."
ttyd -p $PORT bash &
TTYD_PID=$!
sleep 2

# 2. Start ngrok
echo "[+] Starting ngrok tunnel on port $PORT..."
ngrok http $PORT > /dev/null &
NGROK_PID=$!
sleep 5

# 3. Fetch ngrok public URL
echo "[+] Fetching ngrok public URL..."
NGROK_URL=""
for i in {1..10}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    if [[ "$NGROK_URL" == https* ]]; then
        break
    fi
    sleep 1
done

# 4. Check URL
if [[ -z "$NGROK_URL" || "$NGROK_URL" == "null" ]]; then
    echo "[-] Failed to get ngrok URL."
    kill $NGROK_PID 2>/dev/null
    kill $TTYD_PID 2>/dev/null
    exit 1
fi

echo "[+] ngrok URL is: $NGROK_URL"

# 5. Send Email
echo "Your remote terminal is available at: $NGROK_URL" | mail -s "$SUBJECT" -r "$EMAIL" "$EMAIL"

echo "[+] Email sent to $EMAIL"

