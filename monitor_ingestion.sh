#!/bin/bash
# Monitor ingestion progress in real-time

echo "==================================================================="
echo "CHATGPT INGESTION MONITOR"
echo "==================================================================="
echo

# Check if process is running
if ps aux | grep -q "[i]ngest-chatgpt"; then
    PID=$(ps aux | grep "[i]ngest-chatgpt" | awk '{print $2}')
    echo "✓ Ingestion process running (PID: $PID)"
    
    # Show resource usage
    ps -p $PID -o pid,pcpu,pmem,etime,cmd --no-headers | head -1 | while read pid cpu mem time cmd; do
        echo "  CPU: ${cpu}%  |  Memory: ${mem}%  |  Runtime: ${time}"
    done
    echo
else
    echo "✗ No ingestion process found"
    echo "Start with: python main.py ingest-chatgpt /home/chris/data/conversations-000.json -o chatgpt_graph.json -p"
    exit 1
fi

# Monitor output file growth
if [ -f "ingestion_detailed.log" ]; then
    LINES=$(wc -l < ingestion_detailed.log)
    echo "Log file: ingestion_detailed.log ($LINES lines)"
    echo
    
    echo "--- Latest output (refreshing every 3 seconds) ---"
    echo
    
    # Keep tailing the log
    tail -f ingestion_detailed.log 2>/dev/null
else
    echo "Waiting for log output..."
    echo "(Python may buffer output - please wait 30-60 seconds)"
    echo
    
    # Wait and keep checking
    for i in {1..20}; do
        sleep 3
        if [ -f "ingestion_detailed.log" ] && [ $(wc -l < ingestion_detailed.log) -gt 5 ]; then
            echo
            echo "Output detected! Latest content:"
            echo
            tail -30 ingestion_detailed.log
            echo
            echo "=== Live tail (Ctrl+C to exit) ==="
            tail -f ingestion_detailed.log
            exit 0
        fi
        echo -n "."
    done
    
    echo
    echo "Note: Output may still be buffered. The process is running."
    echo "Check later with: tail -f ingestion_detailed.log"
fi
