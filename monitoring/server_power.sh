systemd-inhibit --what="sleep" --why="Power Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> '
echo "date,time,power_watts"

while true; do
    POWER=$(snmpget -v 1 -c <SNMP_COMMUNITY> -OvnQ \
        <PDU_HOST>:<SNMP_PORT> <POWER_OID> 2>/dev/null)

    echo "$(date +%Y-%m-%d),$(date +%H:%M:%S),$POWER"
    sleep 1
done
' | tee -a ~/server_power_readings.csv
